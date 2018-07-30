import tensorflow
import numpy
import os
import random
import skimage.io
import sklearn.preprocessing

log_dir='log/'
model_dir='model/'
batch_size=100
max_step=60000
repeat_times=10
init_lr=0.001
decay_rate=0.01
input_dim=28
hidden_dim=40
output_dim=10

(train_data,train_label),(test_data,test_label)=tensorflow.keras.datasets.mnist.load_data()
OneHotEncoder=sklearn.preprocessing.OneHotEncoder()
OneHotEncoder.fit(train_label.reshape(-1,1))
train_label=OneHotEncoder.transform(train_label.reshape(-1,1)).toarray()
test_label=OneHotEncoder.transform(test_label.reshape(-1,1)).toarray()

def gru(x,h_old):
    with tensorflow.variable_scope('gru',reuse=tensorflow.AUTO_REUSE):
        rxw=tensorflow.get_variable('rxw',[input_dim,hidden_dim])
        rhw=tensorflow.get_variable('rhw',[hidden_dim,hidden_dim])
        rb=tensorflow.get_variable('rb',hidden_dim)
        rxw_r=tensorflow.matmul(x,rxw)
        rhw_r=tensorflow.matmul(h_old,rhw)
        rz=rxw_r+rhw_r+rb
        r=tensorflow.nn.sigmoid(rz)

        uxw=tensorflow.get_variable('uxw',[input_dim,hidden_dim])
        uhw=tensorflow.get_variable('uhw',[hidden_dim,hidden_dim])
        ub=tensorflow.get_variable('ub',hidden_dim)
        uxw_r=tensorflow.matmul(x,uxw)
        uhw_r=tensorflow.matmul(h_old,uhw)
        uz=uxw_r+uhw_r+ub
        u=tensorflow.nn.sigmoid(uz)

        txw=tensorflow.get_variable('txw',[input_dim,hidden_dim])
        thw=tensorflow.get_variable('thw',[hidden_dim,hidden_dim])
        tb=tensorflow.get_variable('tb',hidden_dim)
        txw_r=tensorflow.matmul(x,txw)
        thw_r=tensorflow.matmul(r*h_old,thw)
        tz=txw_r+thw_r+tb
        t=tensorflow.nn.tanh(tz)

        h_new=(1-u)*h_old+u*t
    return h_new

def predict(x):
    with tensorflow.variable_scope('predict',reuse=tensorflow.AUTO_REUSE):
        w=tensorflow.get_variable('w',[hidden_dim,output_dim])
        b=tensorflow.get_variable('b',output_dim)
        z=tensorflow.matmul(x,w)+b
    return z

def process(data,init_hide):
    encode_output=[]
    for i in range(28):
        if i==0:
            output_hide=gru(data[:,i],init_hide)
            encode_output.append(output_hide)
        else:
            output_hide=gru(data[:,i],output_hide)
            encode_output.append(output_hide) 
    predict_output=predict(output_hide)
    return predict_output

len([x.name for x in tensorflow.get_collection(tensorflow.GraphKeys.GLOBAL_VARIABLES)])

input_data=tensorflow.placeholder(tensorflow.float32,[None,28,28],name='input_data')
input_label=tensorflow.placeholder(tensorflow.float32,[None,10],name='input_label')
global_step = tensorflow.get_variable('global_step',initializer=0, trainable=False)
learning_rate=tensorflow.train.exponential_decay(init_lr,global_step,max_step,decay_rate)
init_hide=tensorflow.placeholder(tensorflow.float32,[None,hidden_dim],name='init_hide')

process_result=process(input_data,init_hide)

loss=tensorflow.losses.softmax_cross_entropy(input_label,process_result)

minimize=tensorflow.train.AdamOptimizer(learning_rate).minimize(loss,global_step=global_step,name='minimize')

# accuracy,_=tensorflow.metrics.accuracy(input_label,tensorflow.nn.softmax(process_result))
accuracy = tensorflow.reduce_mean(tensorflow.cast(tensorflow.equal(tensorflow.argmax(tensorflow.nn.softmax(process_result), 1), tensorflow.argmax(input_label, 1)), tensorflow.float32))

Session=tensorflow.Session()
Session.run(tensorflow.global_variables_initializer())
# Session.run(tensorflow.local_variables_initializer())

tensorflow.summary.scalar('loss', loss)
tensorflow.summary.scalar('accuracy', accuracy)
merge_all = tensorflow.summary.merge_all()
FileWriter = tensorflow.summary.FileWriter(log_dir, Session.graph)

num = train_data.shape[0] // batch_size
for i in range(max_step*repeat_times//batch_size+1):
    temp_train = train_data[i % num * batch_size:i % num * batch_size + batch_size,:]
    temp_label = train_label[i % num * batch_size:i % num * batch_size + batch_size,:]
    Session.run(minimize,feed_dict={input_data:temp_train,input_label:temp_label,init_hide:numpy.zeros([batch_size,hidden_dim])})
    if Session.run(global_step)%100==1:
        summary = Session.run(merge_all, feed_dict={input_data:test_data,input_label:test_label,init_hide:numpy.zeros([test_data.shape[0],hidden_dim])})
        FileWriter.add_summary(summary, Session.run(global_step))
    print(Session.run(global_step))