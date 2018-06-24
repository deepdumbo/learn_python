import tensorflow
import numpy 
import pandas
import skimage.io
import sklearn
import os
import sys
import cv2
import random
import time

data_dir='E:/SRAD2018/train'
log_dir='log/'
model_dir='model/'
image_dim=501
init_lr=0.001
decay_rate=0.01
max_step=10001
input_channel=1
encode_channel1=8
encode_channel2=16
encode_channel3=32
encode_channel4=64
output_channel=1

def test(x,is_train):
    with tensorflow.variable_scope('encode'):
        encode_w1=tensorflow.get_variable('w1', [3,3,input_channel,encode_channel1], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        encode_b1=tensorflow.get_variable('b1', encode_channel1, initializer=tensorflow.constant_initializer(0))
        encode_z1=tensorflow.nn.conv2d((x-128)/128,encode_w1,[1,2,2,1],'SAME')+encode_b1
        encode_z1=tensorflow.layers.batch_normalization(encode_z1,training=is_train,name='bn1')
        encode_z1=tensorflow.nn.selu(encode_z1)

        encode_w2=tensorflow.get_variable('w2', [3,3,encode_channel1,encode_channel2], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        encode_b2=tensorflow.get_variable('b2', encode_channel2, initializer=tensorflow.constant_initializer(0))
        encode_z2=tensorflow.nn.conv2d(encode_z1,encode_w2,[1,2,2,1],'SAME')+encode_b2
        encode_z2=tensorflow.layers.batch_normalization(encode_z2,training=is_train,name='bn2')
        encode_z2=tensorflow.nn.selu(encode_z2)

        encode_w3=tensorflow.get_variable('w3', [3,3,encode_channel2,encode_channel3], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        encode_b3=tensorflow.get_variable('b3', encode_channel3, initializer=tensorflow.constant_initializer(0))
        encode_z3=tensorflow.nn.conv2d(encode_z2,encode_w3,[1,2,2,1],'SAME')+encode_b3
        encode_z3=tensorflow.layers.batch_normalization(encode_z3,training=is_train,name='bn3')
        encode_z3=tensorflow.nn.selu(encode_z3)

        encode_w4=tensorflow.get_variable('w4', [3,3,encode_channel3,encode_channel4], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        encode_b4=tensorflow.get_variable('b4', encode_channel4, initializer=tensorflow.constant_initializer(0))
        encode_z4=tensorflow.nn.conv2d(encode_z3,encode_w4,[1,2,2,1],'SAME')+encode_b4
        encode_z4=tensorflow.layers.batch_normalization(encode_z4,training=is_train,name='bn4')
        encode_z4=tensorflow.nn.tanh(encode_z4)

    with tensorflow.variable_scope('decode'):
        decode_w1=tensorflow.get_variable('w1', [3,3,encode_channel3,encode_channel4], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        decode_b1=tensorflow.get_variable('b1', encode_channel3, initializer=tensorflow.constant_initializer(0))
        decode_z1=tensorflow.nn.conv2d_transpose(encode_z4,decode_w1,tensorflow.shape(encode_z3),[1,2,2,1],'SAME')+decode_b1
        decode_z1=tensorflow.layers.batch_normalization(decode_z1,training=is_train,name='bn1')
        decode_z1=tensorflow.nn.selu(decode_z1)

        decode_w2=tensorflow.get_variable('w2', [3,3,encode_channel2,encode_channel3], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        decode_b2=tensorflow.get_variable('b2', encode_channel2, initializer=tensorflow.constant_initializer(0))
        decode_z2=tensorflow.nn.conv2d_transpose(decode_z1,decode_w2,tensorflow.shape(encode_z2),[1,2,2,1],'SAME')+decode_b2
        decode_z2=tensorflow.layers.batch_normalization(decode_z2,training=is_train,name='bn2')
        decode_z2=tensorflow.nn.selu(decode_z2)

        decode_w3=tensorflow.get_variable('w3', [3,3,encode_channel1,encode_channel2], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        decode_b3=tensorflow.get_variable('b3', encode_channel1, initializer=tensorflow.constant_initializer(0))
        decode_z3=tensorflow.nn.conv2d_transpose(decode_z2,decode_w3,tensorflow.shape(encode_z1),[1,2,2,1],'SAME')+decode_b3
        decode_z3=tensorflow.layers.batch_normalization(decode_z3,training=is_train,name='bn3')
        decode_z3=tensorflow.nn.selu(decode_z3)

        decode_w4=tensorflow.get_variable('w4', [3,3,input_channel,encode_channel1], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        decode_b4=tensorflow.get_variable('b4', input_channel, initializer=tensorflow.constant_initializer(0))
        decode_z4=tensorflow.nn.conv2d_transpose(decode_z3,decode_w4,tensorflow.shape(x),[1,2,2,1],'SAME')+decode_b4
        decode_z4=tensorflow.layers.batch_normalization(decode_z4,training=is_train,name='bn4')
        decode_z4=tensorflow.nn.tanh(decode_z4)

    return encode_z1, encode_z2, encode_z3, encode_z4, decode_z1, decode_z2, decode_z3, decode_z4*128+128

input_image=tensorflow.placeholder(tensorflow.float32,[None,image_dim,image_dim,1])
is_train=tensorflow.placeholder(tensorflow.bool)
global_step=0
learn_rate=tensorflow.train.exponential_decay(init_lr,global_step,max_step,0.01)
encode_h1, encode_h2, encode_h3, encode_h4, decode_h1, decode_h2, decode_h3, decode_h4=test(input_image,is_train)

# loss=tensorflow.losses.mean_squared_error(input_image,decode_h4)
loss1=tensorflow.losses.mean_squared_error(input_image,decode_h4)
loss2=tensorflow.losses.mean_squared_error(encode_h1,decode_h3)
loss3=tensorflow.losses.mean_squared_error(encode_h2,decode_h2)
loss4=tensorflow.losses.mean_squared_error(encode_h3,decode_h1)

loss1_var=tensorflow.get_collection(tensorflow.GraphKeys.TRAINABLE_VARIABLES)
loss2_var=tensorflow.get_collection(tensorflow.GraphKeys.TRAINABLE_VARIABLES)
loss2_var.pop(0)
loss2_var.pop(0)
loss2_var.pop(-1)
loss2_var.pop(-1)
loss3_var=tensorflow.get_collection(tensorflow.GraphKeys.TRAINABLE_VARIABLES)
loss3_var.pop(0)
loss3_var.pop(0)
loss3_var.pop(0)
loss3_var.pop(0)
loss3_var.pop(-1)
loss3_var.pop(-1)
loss3_var.pop(-1)
loss3_var.pop(-1)
loss4_var=tensorflow.get_collection(tensorflow.GraphKeys.TRAINABLE_VARIABLES)
loss4_var.pop(0)
loss4_var.pop(0)
loss4_var.pop(0)
loss4_var.pop(0)
loss4_var.pop(0)
loss4_var.pop(0)
loss4_var.pop(-1)
loss4_var.pop(-1)
loss4_var.pop(-1)
loss4_var.pop(-1)
loss4_var.pop(-1)
loss4_var.pop(-1)

with tensorflow.control_dependencies(tensorflow.get_collection(tensorflow.GraphKeys.UPDATE_OPS)):
    # minimize=tensorflow.train.AdamOptimizer(learn_rate).minimize(loss)

    AdamOptimizer=tensorflow.train.AdamOptimizer(learn_rate)
    minimize1=AdamOptimizer.minimize(loss1,var_list=loss1_var,name='minimize1')
    minimize2=AdamOptimizer.minimize(loss2,var_list=loss2_var,name='minimize2')
    minimize3=AdamOptimizer.minimize(loss3,var_list=loss3_var,name='minimize3')
    minimize4=AdamOptimizer.minimize(loss4,var_list=loss4_var,name='minimize4')

Saver = tensorflow.train.Saver()

Session=tensorflow.Session()
Session.run(tensorflow.global_variables_initializer())

tensorflow.summary.scalar('loss1', loss1)
tensorflow.summary.scalar('loss2', loss2)
tensorflow.summary.scalar('loss3', loss3)
tensorflow.summary.scalar('loss4', loss4)
tensorflow.summary.image('true_images', input_image, 61)
tensorflow.summary.image('decode_images', decode_h4, 61)
merge_all = tensorflow.summary.merge_all()
FileWriter = tensorflow.summary.FileWriter(log_dir, Session.graph)

for i in range(max_step):
    # lr=tensorflow.train.exponential_decay(init_lr,i,max_step,0.01)
    # AdamOptimizer._lr=lr
    all_file=os.listdir(data_dir)
    pick_one_file=random.sample(all_file,1)[0]
    one_file=os.path.join(data_dir,pick_one_file)
    one_all_rad=os.listdir(one_file)
    pick_one_rad=random.sample(one_all_rad,1)[0]
    one_rad=os.path.join(one_file,pick_one_rad)
    all_image_dir=[os.path.join(one_rad,x) for x in os.listdir(one_rad)]
    all_image_dir.sort()
    all_image=[cv2.imread(x) for x in all_image_dir]
    all_image=numpy.array(all_image)

    try:
        for j in range(all_image.shape[0]):
            # Session.run(minimize,feed_dict={input_image:all_image[j:j+1,:,:,0:1],is_train:True})
            Session.run(minimize4,feed_dict={input_image:all_image[j:j+1,:,:,0:1],is_train:True})
            Session.run(minimize3,feed_dict={input_image:all_image[j:j+1,:,:,0:1],is_train:True})
            Session.run(minimize2,feed_dict={input_image:all_image[j:j+1,:,:,0:1],is_train:True})
            Session.run(minimize1,feed_dict={input_image:all_image[j:j+1,:,:,0:1],is_train:True})

        if i%100==0:
            for image in all_image[:,:,:,0:1]:
                cv2.imshow('true image', image)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                time.sleep(0.1)
            cv2.destroyAllWindows()

            for image in Session.run(decode_h4,feed_dict={input_image:all_image[:,:,:,0:1],is_train:False}):
                cv2.imshow('decode image', image)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                time.sleep(0.1)
            cv2.destroyAllWindows()

            summary = Session.run(merge_all, feed_dict={input_image:all_image[:,:,:,0:1],is_train:False})
            FileWriter.add_summary(summary, i)
            Saver.save(Session, model_dir, i)

            # print(Session.run(loss,feed_dict={input_image:all_image[:,:,:,0:1],is_train:False}))
            print(Session.run(loss1,feed_dict={input_image:all_image[:,:,:,0:1],is_train:False}))
            print(Session.run(loss2,feed_dict={input_image:all_image[:,:,:,0:1],is_train:False}))
            print(Session.run(loss3,feed_dict={input_image:all_image[:,:,:,0:1],is_train:False}))
            print(Session.run(loss4,feed_dict={input_image:all_image[:,:,:,0:1],is_train:False}))

        print(i)

    except:
            print('数据异常:',one_rad,'第%s张图片'%(j+1))