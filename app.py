from flask import Flask, render_template, request, redirect, url_for, session
import os, pandas as pd, numpy as np, matplotlib.pyplot as plt, seaborn as sns, random, string
import hdf5storage as hd
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest

app = Flask(__name__)
app.secret_key = os.urandom(24)

filename = ''
filename_pca = ''

@app.route('/',  methods=['GET','POST'])
def index():
    
    return render_template('index.html')

# -- Upload Data --
@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'GET':
        if 'username' in session:
            return redirect('/uploadnone')
        files = [f for f in os.listdir('static/data') if '.csv' in f or '.mat' in f]
        # files = []
        # for r, d, f in os.walk('static/data'):
        #     for file in f:
        #         if '.csv' in file or '.mat' in file:
        #             files.append(file)
        return render_template('upload.html', files=files)

@app.route('/uploadnone', methods=['GET','POST'])
def uploadnone():
    if request.method == 'GET':
        files = [f for f in os.listdir('static/data') if '.csv' in f or '.mat' in f]
        # directory = 'static/data/' + session['username']
        # if not os.path.exists(directory):
        #     os.makedirs(directory)
        # filesPeneliti = [f for f in os.listdir(directory) if '.csv' in f or '.mat' in f]
        return render_template('uploadnone.html', files=files)
    elif request.method == 'POST':
        file = request.files['file']
        file.save(os.path.join('static/data/',file.filename))
        return redirect('/uploadnone')

# -- Choose Data --
@app.route('/choose')
def choose():
    file = request.args.get('data')
    filepath = ''
    # if 'username' in session:
    #     if file in os.listdir('static/data/' + session['username']):
    #         session['data'] = 'static/data/' + session['username'] + '/' + file
    #     elif file in os.listdir('static/data/'):
    #         session['data'] = 'static/data/' + file
    # else:
    session['data'] = 'static/data/' + file
        
    # session['data'] = file
    return redirect('display')
    
#  -- Display Choosen Data --
@app.route('/display')
def display():
    global filename_pca
    if os.path.isfile(os.path.join('static/img/', filename_pca)) :
        os.remove(os.path.join('static/img/', filename_pca))
    if session['data'].split('.')[-1] == 'csv':
        df = pd.read_csv(session['data'])
    elif session['data'].split('.')[-1] == 'mat':
        mat = hd.loadmat(session['data'])
        X = pd.DataFrame(mat['X'])
        Y = pd.DataFrame(mat['y'])
        Y.rename(columns={0: 'CLASS'}, inplace=True)
        df = pd.concat([X,Y], axis=1)
    shape = df.shape
    desc = df.describe().values
    descCol = ['count','mean','std','min','25%','50%','75%','max']
    for idx in range(len (desc)):
        row = list(desc[idx])
        row.insert(0,descCol[idx])
    print(desc[0])

    # -- Standarisasi Data --
    kelas = df.columns[-1]
    print(df.columns)
    sb_x = df.iloc[:,:-2]
    sb_y = df.loc[:,kelas]
    sb_x = StandardScaler().fit_transform(sb_x)

    pca = PCA(n_components=2)
    attr_x = pca.fit_transform(sb_x)
    # print(attr_x)
    red_data = pd.DataFrame(attr_x, columns = ['A','B'])
    print(red_data.shape)
    print(df.loc[:,kelas].shape)
    print(df.loc[:,kelas])
        
    finalData = pd.concat([red_data, df.loc[:,kelas]], axis=1)

    # print(red_data.values)

    fig = plt.figure(figsize = (8,8))
    ax = fig.add_subplot(1,1,1)
    ax.set_xlabel('A', fontsize=15)
    ax.set_ylabel('B', fontsize=15)
    outcomes = [1,0]
    colors = ['r','g']
    for Outcome, color in zip(outcomes,colors):
        index = finalData[kelas] == Outcome
        ax.scatter(finalData.loc[index,'A'],finalData.loc[index,'B'],c=color,s=50)
        ax.legend(outcomes)
        ax.grid()

    #  Random filename
    filename_pca = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    filename_pca = filename_pca + '.png'
    # print(filename)
    plt.savefig(os.path.join('static/img/', filename_pca))
    filepath = 'img/' + filename_pca
    
    return render_template('display.html', data=df.values, column=df.columns, shape=shape, descr=desc, desccol=descCol, filepath=filepath)

@app.route('/forest', methods=['GET','POST'])
def forest():
    print(session['data'])
    if session['data'].split('.')[-1] == 'csv':
        data = pd.read_csv(session['data'])
    elif session['data'].split('.')[-1] == 'mat':
        mat = hd.loadmat(session['data'])
        X = pd.DataFrame(mat['X'])
        Y = pd.DataFrame(mat['y'])
        Y.rename(columns={0: 'CLASS'}, inplace=True)
        data = pd.concat([X,Y], axis=1)

    global filename
    if os.path.isfile(os.path.join('static/img/', filename)) :
        os.remove(os.path.join('static/img/', filename))
    
    if request.method == 'GET':
        return render_template('forest.html', column=data.columns)
    else:
        
        kelas = request.form['kelas']
        normal = request.form['normal']
        abnormal = request.form['abnormal']
        t_size = float(request.form['tsize'])/100
        cont = float(request.form['cont'])/100
        n_tree = int(request.form['tree'])
        samples = int(request.form['sample'])
        

        # Normal Abnormal
        dt_normal=data.loc[data[kelas]==int(normal)]
        dt_abnormal=data.loc[data[kelas]==int(abnormal)]

        print(dt_normal)

        # Split Data
        normal_train, normal_test = train_test_split(dt_normal, test_size=t_size,random_state=42)
        abnormal_train, abnormal_test = train_test_split(dt_abnormal, test_size=t_size,random_state=42)
        train = pd.concat([normal_train, abnormal_train])
        test = pd.concat([normal_test, abnormal_test])
        # train[kelas] = train[kelas].map({0:1,1:-1})
        data[kelas] = data[kelas].map({0:1,1:-1})
        test[kelas] = test[kelas].map({0:1,1:-1})


        # Model
        model = IsolationForest(n_estimators=n_tree, contamination=cont, max_samples=samples)
        pred = model.fit_predict(data.drop([kelas],axis=1))
        print(pred)
        
        # # Model 2
        model2 = IsolationForest(n_estimators=n_tree, contamination=cont, max_samples=samples)
        model2.fit(train.drop([kelas],axis=1))
        pred2=model2.predict(test.drop([kelas],axis=1))

        # # Hasil Prediksi
        dt=data.drop([kelas], axis=1)
        df_pred=pd.DataFrame(pred)
        df_pred.columns=[kelas]
        dt=pd.concat([dt,df_pred],axis=1)

        # Confusion Matrix
        cm = confusion_matrix(data[kelas], pred)
        df_cm = pd.DataFrame(cm,['Anomali','Normal'],['Prediksi Anomali','Prediksi Normal'])
        plt.figure(figsize = (6,4))
        sns.set(font_scale=1.2)
        sns.heatmap(df_cm, annot=True, annot_kws={'size':16},fmt='g')
        
        # Random filename
        filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        filename = filename + '.png'
        # print(filename)
        plt.savefig(os.path.join('static/img/', filename))

        plt.clf()

        # Confusion Matrix 2
        cm2 = confusion_matrix(test[kelas], pred2)
        df_cm2 = pd.DataFrame(cm2,['Anomali','Normal'],['Prediksi Anomali','Prediksi Normal'])
        plt.figure(figsize = (6,4))
        sns.set(font_scale=1.2)
        sns.heatmap(df_cm2, annot=True, annot_kws={'size':16},fmt='g')

        # Random filename
        filename2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        filename2 = filename2 + '.png'
        # print(filename)
        plt.savefig(os.path.join('static/imgv2/', filename2))
        
        # Convert to Dataframe 
        df_pred=pd.DataFrame(pred)
        df_pred2=pd.DataFrame(pred2)
    
        # Metrik Evaluasi 1
        f1_s = f1_score(data.Outcome, df_pred, average='weighted')
        ps = precision_score(data.Outcome, df_pred, average='weighted')
        rs = recall_score(data.Outcome, df_pred, average='weighted') 

        # Metrik Evaluasi 2
        f1_s1 = f1_score(test.Outcome, df_pred2, average='weighted')
        ps1 = precision_score(test.Outcome, df_pred2, average='weighted')
        rs1 = recall_score(test.Outcome, df_pred2, average='weighted') 

        # tp, fp, fn, tn = cm.ravel()
        # rec=tp/(tp+fn)
        rs=round(rs,3)
        rs1=round(rs1,3)
        # prec=tp/(tp+fp)
        ps=round(ps,3)
        ps1=round(ps1,3)
        # f1_score=2*((prec*rec)/(prec+rec))
        f1_s=round(f1_s,3)
        f1_s1=round(f1_s1,3)

        filepath = 'img/' + filename
        filepath2 = 'imgv2/' + filename2

        return render_template('forest.html',
            tsize=int(t_size * 100),
            cont=int(cont * 100),
            tree=n_tree,
            sample=samples,
            dt=dt.values,
            column=dt.columns,
            cm=df_cm,
            ps=ps,
            rs=rs,
            f1_s=f1_s,
            ps1=ps1,
            rs1=rs1,
            f1_s1=f1_s1,
            kelas=kelas,
            filepath=filepath,
            filepath2=filepath2)

@app.route('/login', methods=['POST'])
def login():
    print(request.form)
    username = request.form['username']
    password = request.form['password']
    data = pd.read_csv('static/auth/user.csv')
    record = data.to_dict('records')
    print(record)
    for val in record:
        if val['username'] == username and str(val['password']) == str(password):
            session['username'] = username
            return redirect('/uploadnone')
    return redirect('/upload')

@app.route('/logout')
def logout():
   session.clear()
   return redirect('/')

@app.route('/daftar', methods=['POST'])
def daftar():
    data = pd.read_csv('static/auth/user.csv')
    username = request.form['username']
    password = request.form['password']
    user = {
        'username': [username],
        'password': [password]
    }
    user = pd.DataFrame.from_dict(user)
    data = pd.concat([data, user])
    data.to_csv('static/auth/user.csv', index=False)
    return redirect('/upload')

@app.route('/guide')
def guide():

    return render_template('guide.html')

if __name__ == '__main__':
    app.run()
