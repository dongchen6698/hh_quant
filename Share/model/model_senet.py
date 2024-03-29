import tensorflow as tf
from .layers import DnnLayer, BitWiseSeNet


class QuantModel(tf.keras.Model):
    def __init__(self, config, **kwargs):
        super(QuantModel, self).__init__(**kwargs)
        self.config = config
        self.lookup_layers = {}
        self.embedding_layers = {}

        # 创建整数特征的查找层和嵌入层
        for feature_name, vocab in self.config.get("integer_categorical_features_with_vocab").items():
            self.lookup_layers[feature_name] = tf.keras.layers.IntegerLookup(vocabulary=vocab, name=f"{feature_name}_lookup")
            self.embedding_layers[feature_name] = tf.keras.layers.Embedding(
                input_dim=len(vocab) + 1,
                output_dim=self.config.get("feature_embedding_dims", 4),
                embeddings_initializer=tf.keras.initializers.glorot_normal(self.config.get("seed", 1024)),
                name=f"{feature_name}_embedding",
            )
        # 创建字符串特征的查找层和嵌入层
        for feature_name, vocab in self.config.get("string_categorical_features_with_vocab").items():
            self.lookup_layers[feature_name] = tf.keras.layers.StringLookup(vocabulary=vocab, name=f"{feature_name}_lookup")
            self.embedding_layers[feature_name] = tf.keras.layers.Embedding(
                input_dim=len(vocab) + 1,
                output_dim=self.config.get("feature_embedding_dims", 4),
                embeddings_initializer=tf.keras.initializers.glorot_normal(self.config.get("seed", 1024)),
                name=f"{feature_name}_embedding",
            )

        # 自定义层相关
        self.deep_part = tf.keras.Sequential(
            [
                BitWiseSeNet(
                    reduction_ratio=self.config.get("reduction_ratio", 3),
                    l2_reg=self.config.get("l2_reg", 0.0),
                    seed=self.config.get("seed", 1024),
                ),
                DnnLayer(
                    hidden_units=self.config.get("dnn_hidden_units", [64, 32]),
                    activation=self.config.get("dnn_activation", "relu"),
                    dropout_rate=self.config.get("dnn_dropout", 0.2),
                    use_bn=self.config.get("dnn_use_bn", True),
                    l2_reg=self.config.get("l2_reg", 0.001),
                    seed=self.config.get("seed", 1024),
                ),
            ]
        )

        self.wide_output_layer = tf.keras.layers.Dense(1, activation=None)
        self.deep_output_layer = tf.keras.layers.Dense(1, activation=None)

    def get_sparse_dense_features(self, inputs):
        sparse_features = []  # list of [B, emb]
        dense_features = []  # [B, N]
        for feature_name, feature_value in inputs.items():
            if feature_name in self.lookup_layers:
                lookup_layer = self.lookup_layers[feature_name]
                embedding_layer = self.embedding_layers[feature_name]
                encode_feature = embedding_layer(lookup_layer(feature_value))
                sparse_features.append(encode_feature)
            else:
                dense_features.append(feature_value)
        return sparse_features, dense_features

    def call(self, inputs, training=False):
        if not isinstance(inputs, dict):
            raise ValueError("The inputs to the model should be a dictionary where keys are feature names.")

        # 处理Deep侧特征
        sparse_features, dense_features = self.get_sparse_dense_features(inputs)
        dense_emb = tf.stack(dense_features, axis=-1)
        sparse_emb = tf.concat(sparse_features, axis=-1)

        # Wide..........................................................................................
        wide_logit = self.wide_output_layer(dense_emb)

        # Deep..........................................................................................
        deep_input = tf.concat([sparse_emb, dense_emb], axis=-1)
        deep_output = self.deep_part(deep_input)
        deep_logit = self.deep_output_layer(deep_output)

        # Output........................................................................................
        final_logit = deep_logit + wide_logit
        return final_logit

    def get_config(self):
        config = super(QuantModel, self).get_config()
        config.update({"config": self.config})
        return config
