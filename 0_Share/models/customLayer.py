import tensorflow as tf
from tensorflow.keras.layers import Layer, Dense


class SENetLayer(Layer):
    def __init__(self, reduction_ratio=8, **kwargs):
        super(SENetLayer, self).__init__(**kwargs)
        self.reduction_ratio = reduction_ratio

    def build(self, input_shape):
        self.channel_axis = -1
        self.channels = input_shape[self.channel_axis]
        assert self.channels % self.reduction_ratio == 0, "channels must be divisible by reduction_ratio"
        self.global_average = tf.keras.layers.GlobalAveragePooling2D()
        self.dense1 = Dense(self.channels // self.reduction_ratio, activation="relu")
        self.dense2 = Dense(self.channels, activation="sigmoid")

    def call(self, inputs):
        se = self.global_average(inputs)
        se = tf.reshape(se, (-1, 1, 1, self.channels))
        se = self.dense1(se)
        se = self.dense2(se)
        return inputs * se

    def get_config(self):
        config = super(SENetLayer, self).get_config()
        config.update({"reduction_ratio": self.reduction_ratio})
        return config
