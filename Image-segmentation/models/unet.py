import math
from keras.losses import categorical_crossentropy
from keras.backend import reshape
from keras_contrib.losses.jaccard import jaccard_distance
from keras.models import Model
from keras.layers import (Input,
                         Conv2D,
                         MaxPooling2D,
                         Conv2DTranspose,
                         Concatenate,
                         Cropping2D,
                         BatchNormalization)

class UNET():

    def __init__(self,
                 input_shape,
                 num_classes,
                 filter_list,
                 kernel_size,
                 batch_norm=False,
                 initializer='glorot_uniform'):
        '''
        UNET model
        '''
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.filter_list = filter_list
        self.kernel_size = kernel_size
        self.num_passes = len(self.filter_list)
        self.batch_norm = batch_norm
        self.initializer = initializer
        self.copies = list()

        # model
        input = Input(shape=self.input_shape)
        # down
        x = input
        for f in self.filter_list:
            x, copy = self.down_pass(x,f)
            self.copies.append(copy)

        x = self.bottom(x,self.filter_list[-1]*2)
        self.copies.reverse()
        self.filter_list.reverse()
        # up
        for i, (f, copy) in enumerate(zip(self.filter_list,self.copies),1):
            x = self.up_pass(x,copy,f,last = i == self.num_passes)

        predictions = Conv2D(filters=self.num_classes,
                             kernel_size=(1,1),
                             activation='softmax',
                             padding='same')(x)
        self.model = Model(inputs=input,outputs=predictions)

    def down_pass(self,input,n_filters):
        '''Down pass'''
        output = Conv2D(n_filters,self.kernel_size,activation='relu',padding='same')(input)
        output = Conv2D(n_filters,self.kernel_size,activation='relu',padding='same')(output)
        copy = output#Cropping2D(cropping=(4,4))(output)
        if self.batch_norm:
            output = BatchNormalization()(output)
        output = MaxPooling2D()(output)
        return output, copy

    def up_pass(self,input,copy,n_filters, last=False):
        '''Up pass'''
        output = Concatenate(axis=-1)([input,copy])
        if self.batch_norm:
            output = BatchNormalization()(output)
        output = Conv2D(n_filters,self.kernel_size,activation='relu',padding='same')(output)
        output = Conv2D(n_filters,self.kernel_size,activation='relu',padding='same')(output)
        if not last:
            output = Conv2DTranspose(n_filters//2,self.kernel_size,strides=(2,2),padding='same')(output)
        return output

    def bottom(self,input,n_filters):
        output = Conv2D(n_filters,self.kernel_size,activation='relu',padding='same')(input)
        output = Conv2D(n_filters,self.kernel_size,activation='relu',padding='same')(output)
        output = Conv2DTranspose(n_filters//2,self.kernel_size,strides=(2,2),padding='same')(output)
        return output

def make_Jaccard_XEntropy_Loss(alpha=0.5):
    def JX_Loss(y_true,y_pred):
        xe_loss = categorical_crossentropy(y_true,y_pred)
        jac_dis = jaccard_distance(y_true,y_pred)
        return alpha*jac_dis + (1.-alpha)*xe_loss
    return JX_Loss


def main():
    unet = UNET((256,256,1),3,[64,128,256,512],3)
    unet.model.summary()

if __name__ == '__main__':
    main()
