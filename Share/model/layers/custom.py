import tensorflow as tf
from tensorflow.keras.initializers import glorot_normal, Zeros


class SeNetLayer(tf.keras.layers.Layer):
    def __init__(self, reduction_ratio=3, seed=1024, **kwargs):
        super(SeNetLayer, self).__init__(**kwargs)
        self.reduction_ratio = reduction_ratio
        self.seed = seed

    def build(self, input_shape):
        if not isinstance(input_shape, list) or len(input_shape) < 2:
            raise ValueError("A `Senet` layer should be called on a list of at least 2 inputs")
        self.field_size = len(input_shape)
        self.reduction_size = max(1, self.field_size // self.reduction_ratio)
        self.W_1 = self.add_weight(shape=(self.field_size, self.reduction_size), initializer=glorot_normal(seed=self.seed), trainable=True, name="senet_w_1")
        self.W_2 = self.add_weight(shape=(self.reduction_size, self.field_size), initializer=glorot_normal(seed=self.seed), trainable=True, name="senet_w_2")
        # Be sure to call this somewhere!
        super(SeNetLayer, self).build(input_shape)

    def call(self, inputs, training=False):
        inputs = [tf.expand_dims(i, axis=1) for i in inputs]
        inputs = tf.concat(inputs, axis=1)  # [B, N, dim]
        Z = tf.reduce_mean(inputs, axis=-1)  # [B, N]
        A_1 = tf.nn.relu(tf.matmul(Z, self.W_1))  # [B, x]
        A_2 = 2 * tf.nn.sigmoid(tf.matmul(A_1, self.W_2))  # [B, N]
        scale_inputs = tf.multiply(inputs, tf.expand_dims(A_2, axis=-1))
        output = scale_inputs + inputs  # skip-connection
        return output  # [B, N, dim]

    def get_config(self):
        config = super(SeNetLayer, self).get_config()
        config.update({"reduction_ratio": self.reduction_ratio, "seed": self.seed})
        return config


class CrossNetLayer(tf.keras.layers.Layer):
    def __init__(self, layer_num=2, parameterization="vector", seed=1024, **kwargs):
        super(CrossNetLayer, self).__init__(**kwargs)
        self.layer_num = layer_num
        self.parameterization = parameterization
        self.seed = seed
        print("CrossNet parameterization:", self.parameterization)

    def build(self, input_shape):
        if len(input_shape) != 2:
            raise ValueError(f"Unexpected inputs dimensions {len(input_shape)}, expect to be 2 dimensions")

        # input_shape: (batch_size, feature_dim)
        feature_dim = int(input_shape[-1])

        # 配置crossNet的Kernels
        if self.parameterization == "vector":
            self.kernels = [
                self.add_weight(
                    shape=(feature_dim, 1),
                    initializer=glorot_normal(seed=self.seed),
                    trainable=True,
                    name=f"crossnet_kernel_{i}",
                )
                for i in range(self.layer_num)
            ]
        elif self.parameterization == "matrix":
            self.kernels = [
                self.add_weight(
                    shape=(feature_dim, feature_dim),
                    initializer=glorot_normal(seed=self.seed),
                    trainable=True,
                    name=f"crossnet_kernel_{i}",
                )
                for i in range(self.layer_num)
            ]
        else:  # error
            raise ValueError("parameterization should be 'vector' or 'matrix'")

        # 配置crossNet的Bias
        self.bias = [
            self.add_weight(
                shape=(feature_dim, 1),
                initializer=Zeros(),
                trainable=True,
                name=f"crossnet_bias_{i}",
            )
            for i in range(self.layer_num)
        ]

        # Be sure to call this somewhere!
        super(CrossNetLayer, self).build(input_shape)

    def call(self, inputs, **kwargs):
        x0 = tf.expand_dims(inputs, -1)  # [B, dim, 1]
        xi = x0  # xi: 上一层的输出[B, dim, 1], 初始化xi=x0
        for i in range(self.layer_num):
            if self.parameterization == "vector":
                # xi = x0.trans(xi).wi + bi + xi
                xiw = tf.tensordot(xi, self.kernels[i], axes=(1, 0))
                xi = tf.matmul(x0, xiw) + self.bias[i] + xi
            elif self.parameterization == "matrix":
                xiw = tf.einsum("ij,bjk->bik", self.kernels[i], xi)  # [B, dim, 1]
                xi = x0 * (xiw + self.bias[i]) + xi
            else:  # error
                raise ValueError("parameterization should be 'vector' or 'matrix'")
        output = tf.squeeze(xi, axis=-1)
        return output

    def get_config(self):
        config = super(CrossNetLayer, self).get_config()
        config.update({"layer_num": self.layer_num, "parameterization": self.parameterization, "seed": self.seed})
        return config


class DnnLayer(tf.keras.layers.Layer):
    def __init__(self, hidden_units=[64, 32], activation="relu", dropout_rate=0.2, use_bn=True, seed=1024, **kwargs):
        super(DnnLayer, self).__init__(**kwargs)
        self.hidden_units = hidden_units
        self.activation = activation
        self.dropout_rate = dropout_rate
        self.use_bn = use_bn
        self.seed = seed
        self.dense_layers = []
        self.dropout_layers = []
        self.bn_layers = []

    def build(self, input_shape):
        for units in self.hidden_units:
            self.dense_layers.append(
                tf.keras.layers.Dense(units=units, activation=self.activation, kernel_initializer=glorot_normal(seed=self.seed), bias_initializer=Zeros())
            )
            self.dropout_layers.append(tf.keras.layers.Dropout(rate=self.dropout_rate, seed=self.seed))
            if self.use_bn:
                self.bn_layers.append(tf.keras.layers.BatchNormalization())
        # Be sure to call this somewhere!
        super(DnnLayer, self).build(input_shape)

    def call(self, inputs, training=False):
        # print(f"Dnn Is Training Mode: {training}")
        x = inputs
        for i in range(len(self.hidden_units)):
            x = self.dense_layers[i](x)
            if self.use_bn:
                x = self.bn_layers[i](x, training=training)
            x = self.dropout_layers[i](x, training=training)
        return x

    def get_config(self):
        config = super(DnnLayer, self).get_config()
        config.update(
            {"hidden_units": self.hidden_units, "activation": self.activation, "dropout_rate": self.dropout_rate, "use_bn": self.use_bn, "seed": self.seed}
        )
        return config
