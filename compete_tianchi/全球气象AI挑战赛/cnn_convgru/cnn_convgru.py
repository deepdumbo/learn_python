import tensorflow
import numpy 
import os
import random
import time

# data_dir='E:/SRAD2018/train'
data_dir='/media/zhao/新加卷/SRAD2018/train'
# data_dir='/home/jxzhao/tianchi/SRAD2018/train'
log_dir='log/'
model_dir='model/'
init_lr=0.001
decay_rate=0.01
batch_file=2
batch_rad=2
batch_size=batch_file*batch_rad
max_step=300000//batch_size+1
input_channel=1
encode_channel1=4
encode_channel2=8
encode_channel3=16
encode_channel4=32
output_channel=1

def cnn_encode(x):
    with tensorflow.variable_scope('cnn_encode', reuse=tensorflow.AUTO_REUSE):
        encode_w1=tensorflow.get_variable('w1', [3,3,input_channel,encode_channel1], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        encode_b1=tensorflow.get_variable('b1', encode_channel1, initializer=tensorflow.constant_initializer(0))
        encode_z1=tensorflow.nn.conv2d((x-128)/128,encode_w1,[1,2,2,1],'SAME')+encode_b1
        encode_z1=tensorflow.contrib.layers.layer_norm(encode_z1,scope='ln1')
        encode_z1=tensorflow.nn.selu(encode_z1)

        encode_w2=tensorflow.get_variable('w2', [3,3,encode_channel1,encode_channel2], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        encode_b2=tensorflow.get_variable('b2', encode_channel2, initializer=tensorflow.constant_initializer(0))
        encode_z2=tensorflow.nn.conv2d(encode_z1,encode_w2,[1,2,2,1],'SAME')+encode_b2
        encode_z2=tensorflow.contrib.layers.layer_norm(encode_z2,scope='ln2')
        encode_z2=tensorflow.nn.selu(encode_z2)

        encode_w3=tensorflow.get_variable('w3', [3,3,encode_channel2,encode_channel3], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        encode_b3=tensorflow.get_variable('b3', encode_channel3, initializer=tensorflow.constant_initializer(0))
        encode_z3=tensorflow.nn.conv2d(encode_z2,encode_w3,[1,2,2,1],'SAME')+encode_b3
        encode_z3=tensorflow.contrib.layers.layer_norm(encode_z3,scope='ln3')
        encode_z3=tensorflow.nn.selu(encode_z3)

        encode_w4=tensorflow.get_variable('w4', [3,3,encode_channel3,encode_channel4], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        encode_b4=tensorflow.get_variable('b4', encode_channel4, initializer=tensorflow.constant_initializer(0))
        encode_z4=tensorflow.nn.conv2d(encode_z3,encode_w4,[1,2,2,1],'SAME')+encode_b4
        encode_z4=tensorflow.contrib.layers.layer_norm(encode_z4,scope='ln4')
        encode_z4=tensorflow.nn.tanh(encode_z4, name='encode_image')

    return encode_z4

def cnn_decode(x):
    with tensorflow.variable_scope('cnn_decode',reuse=tensorflow.AUTO_REUSE):
        decode_w1=tensorflow.get_variable('w1', [3,3,encode_channel4,encode_channel3], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        decode_b1=tensorflow.get_variable('b1', encode_channel3, initializer=tensorflow.constant_initializer(0))
        decode_z1=tensorflow.nn.conv2d(tensorflow.image.resize_nearest_neighbor(x,[63,63]),decode_w1,[1,1,1,1],'SAME')+decode_b1
        decode_z1=tensorflow.contrib.layers.layer_norm(decode_z1,scope='ln1')
        decode_z1=tensorflow.nn.selu(decode_z1)

        decode_w2=tensorflow.get_variable('w2', [3,3,encode_channel3,encode_channel2], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        decode_b2=tensorflow.get_variable('b2', encode_channel2, initializer=tensorflow.constant_initializer(0))
        decode_z2=tensorflow.nn.conv2d(tensorflow.image.resize_nearest_neighbor(decode_z1,[126,126]),decode_w2,[1,1,1,1],'SAME')+decode_b2
        decode_z2=tensorflow.contrib.layers.layer_norm(decode_z2,scope='ln2')
        decode_z2=tensorflow.nn.selu(decode_z2)

        decode_w3=tensorflow.get_variable('w3', [3,3,encode_channel2,encode_channel1], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        decode_b3=tensorflow.get_variable('b3', encode_channel1, initializer=tensorflow.constant_initializer(0))
        decode_z3=tensorflow.nn.conv2d(tensorflow.image.resize_nearest_neighbor(decode_z2,[251,251]),decode_w3,[1,1,1,1],'SAME')+decode_b3
        decode_z3=tensorflow.contrib.layers.layer_norm(decode_z3,scope='ln3')
        decode_z3=tensorflow.nn.selu(decode_z3)

        decode_w4=tensorflow.get_variable('w4', [3,3,encode_channel1,input_channel], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        decode_b4=tensorflow.get_variable('b4', input_channel, initializer=tensorflow.constant_initializer(0))
        decode_z4=tensorflow.nn.conv2d(tensorflow.image.resize_nearest_neighbor(decode_z3,[501,501]),decode_w4,[1,1,1,1],'SAME')+decode_b4
        decode_z4=tensorflow.contrib.layers.layer_norm(decode_z4,scope='ln4')
        decode_z4=tensorflow.nn.tanh(decode_z4)
        decode_z4=tensorflow.clip_by_value(decode_z4*128+128,0,255,name='decode_image')

    return decode_z4

def convgru_encode(h_old,x):
    with tensorflow.variable_scope('convgru_encode', reuse=tensorflow.AUTO_REUSE):
        rxw=tensorflow.get_variable('rxw',[3,3,32,32])
        rhw=tensorflow.get_variable('rhw',[3,3,32,32])
        rb=tensorflow.get_variable('rb',32)
        rxw_r=tensorflow.nn.conv2d(x,rxw,[1,1,1,1],'SAME')
        rhw_r=tensorflow.nn.conv2d(h_old,rhw,[1,1,1,1],'SAME')
        r=tensorflow.nn.sigmoid(rxw_r+rhw_r+rb)

        uxw=tensorflow.get_variable('uxw',[3,3,32,32])
        uhw=tensorflow.get_variable('uhw',[3,3,32,32])
        ub=tensorflow.get_variable('ub',32)
        uxw_r=tensorflow.nn.conv2d(x,uxw,[1,1,1,1],'SAME')
        uhw_r=tensorflow.nn.conv2d(h_old,uhw,[1,1,1,1],'SAME')
        u=tensorflow.nn.sigmoid(uxw_r+uhw_r+ub)

        txw=tensorflow.get_variable('txw',[3,3,32,32])
        thw=tensorflow.get_variable('thw',[3,3,32,32])
        tb=tensorflow.get_variable('tb',32)
        txw_r=tensorflow.nn.conv2d(x,txw,[1,1,1,1],'SAME')
        thw_r=tensorflow.nn.conv2d(r*h_old,thw,[1,1,1,1],'SAME')
        t=tensorflow.nn.tanh(txw_r+thw_r+tb)

        h_new=(1-u)*h_old+u*t
        return h_new

def convgru_decode(h_old):
    with tensorflow.variable_scope('convgru_decode', reuse=tensorflow.AUTO_REUSE):
        rhw=tensorflow.get_variable('rhw',[3,3,32,32])
        rb=tensorflow.get_variable('rb',32)
        rhw_r=tensorflow.nn.conv2d(h_old,rhw,[1,1,1,1],'SAME')
        r=tensorflow.nn.sigmoid(rhw_r+rb)

        uhw=tensorflow.get_variable('uhw',[3,3,32,32])
        ub=tensorflow.get_variable('ub',32)
        uhw_r=tensorflow.nn.conv2d(h_old,uhw,[1,1,1,1],'SAME')
        u=tensorflow.nn.sigmoid(uhw_r+ub)

        thw=tensorflow.get_variable('thw',[3,3,32,32])
        tb=tensorflow.get_variable('tb',32)
        thw_r=tensorflow.nn.conv2d(r*h_old,thw,[1,1,1,1],'SAME')
        t=tensorflow.nn.tanh(thw_r+tb)

        h_new=(1-u)*h_old+u*t
        return h_new

def gru_process(input_code):
    all_output_encode=[]
    init_hide=numpy.zeros([batch_size,32,32,32]).astype(numpy.float32)
    for i in range(31):
        if i==0:
            output_hide=convgru_encode(init_hide,input_code[:,i,:,:,:])
            all_output_encode.append(output_hide)
        else:
            output_hide=convgru_encode(output_hide,input_code[:,i,:,:,:])
            all_output_encode.append(output_hide)

    all_output_decode=[]
    for i in range(30):
        output_hide=convgru_decode(output_hide)
        all_output_decode.append(output_hide)

    return all_output_encode, all_output_decode

len([x.name for x in tensorflow.get_collection(tensorflow.GraphKeys.GLOBAL_VARIABLES)])

input_image=tensorflow.placeholder(tensorflow.float32,[batch_size,61,32,32,32],name='input_image')
output_image=tensorflow.placeholder(tensorflow.float32,[None,501,501,1],name='output_image')
global_step = tensorflow.get_variable('global_step',initializer=0, trainable=False)
learning_rate=tensorflow.train.exponential_decay(init_lr,global_step,max_step,decay_rate)

tensorflow.unstack()
cnn_encode_result=cnn_encode(input_image)
gru_result=gru_process(cnn_encode_result)
cnn_decode_result=cnn_decode(gru_result)

loss=tensorflow.losses.mean_squared_error(input_image,cnn_decode_result)

minimize=tensorflow.train.AdamOptimizer(learning_rate).minimize(loss,global_step=global_step,name='minimize')

Saver = tensorflow.train.Saver(max_to_keep=0,filename='cnn_convgru')

Session=tensorflow.Session()
if tensorflow.train.latest_checkpoint(model_dir):
    Saver.restore(Session,tensorflow.train.latest_checkpoint(model_dir))
else:
    Session.run(tensorflow.global_variables_initializer())

tensorflow.summary.scalar('loss', loss)
tensorflow.summary.image('input_images', input_image, 10)
tensorflow.summary.image('output_images', decode_z4, 10)
merge_all = tensorflow.summary.merge_all()
FileWriter = tensorflow.summary.FileWriter(log_dir, Session.graph)

for _ in range(max_step):
    all_file=os.listdir(data_dir)
    pick_one_file=random.sample(all_file,1)[0]
    one_file=os.path.join(data_dir,pick_one_file)
    one_all_rad=os.listdir(one_file)
    pick_one_rad=random.sample(one_all_rad,1)[0]
    one_rad=os.path.join(one_file,pick_one_rad)
    all_image_dir=[os.path.join(one_rad,x) for x in os.listdir(one_rad)]
    all_image_dir.sort()
    Session=tensorflow.Session()
    all_image=[tensorflow.read_file(x) for x in all_image_dir]
    all_image=tensorflow.convert_to_tensor([tensorflow.image.decode_jpeg(x,channels=3) for x in all_image])