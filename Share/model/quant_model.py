from __future__ import division, print_function
import os
import sys

cur_path = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.abspath(os.path.join(cur_path, "..")))
sys.path.append(os.path.abspath(os.path.join(cur_path, "../..")))

import tensorflow as tf
from .layers import SeNetLayer, CrossNetLayer, DnnLayer


class QuantModel(tf.keras.Model):
    def __init__(self, config, **kwargs):
        super(QuantModel, self).__init__(**kwargs)
        self.config = config

        # 添加属性来存储预定义的层
        self.lookup_layers = {}
        self.embedding_layers = {}

        # 创建连续特征的离散化层和嵌入层
        for feature_name, boundaries in self.config.get("numeric_features_with_boundaries").items():
            self.lookup_layers[feature_name] = tf.keras.layers.Discretization(bin_boundaries=boundaries, output_mode="int", name=f"{feature_name}_lookup")
            self.embedding_layers[feature_name] = tf.keras.layers.Embedding(
                input_dim=len(boundaries) + 1, output_dim=self.config.get("feature_embedding_dims", 6), name=f"{feature_name}_embedding"
            )
            # 创建整数特征的查找层和嵌入层
        for feature_name, vocab in self.config.get("integer_categorical_features_with_vocab").items():
            self.lookup_layers[feature_name] = tf.keras.layers.IntegerLookup(vocabulary=vocab, name=f"{feature_name}_lookup")
            self.embedding_layers[feature_name] = tf.keras.layers.Embedding(
                input_dim=len(vocab) + 1, output_dim=self.config.get("feature_embedding_dims", 6), name=f"{feature_name}_embedding"
            )
        # 创建字符串特征的查找层和嵌入层
        for feature_name, vocab in self.config.get("string_categorical_features_with_vocab").items():
            self.lookup_layers[feature_name] = tf.keras.layers.StringLookup(vocabulary=vocab, name=f"{feature_name}_lookup")
            self.embedding_layers[feature_name] = tf.keras.layers.Embedding(
                input_dim=len(vocab) + 1, output_dim=self.config.get("feature_embedding_dims", 6), name=f"{feature_name}_embedding"
            )

            # 自定义层相关
        self.senet_layer = SeNetLayer(
            reduction_ratio=self.config.get("reduction_ratio", 3),
            seed=self.config.get("seed", 1024),
        )
        self.crossnet_layer = CrossNetLayer(
            layer_num=self.config.get("cross_layer_num", 2),
            parameterization=self.config.get("parameterization", "vector"),
            seed=self.config.get("seed", 1024),
        )
        self.dnn_layer = DnnLayer(
            hidden_units=self.config.get("dnn_hidden_units", [64, 32]),
            activation=self.config.get("dnn_activation", "relu"),
            dropout_rate=self.config.get("dnn_dropout", 0.2),
            use_bn=self.config.get("dnn_use_bn", True),
            seed=self.config.get("seed", 1024),
        )
        self.output_layer = tf.keras.layers.Dense(1, activation=None)

    def call(self, inputs, training=False):
        # print(f"QuantModel Is Training Mode: {training}")
        # 确保inputs是一个字典类型，每个键值对应一个特征输入
        if not isinstance(inputs, dict):
            raise ValueError("The inputs to the model should be a dictionary where keys are feature names.")
        encoded_features = []
        # 现在使用已经实例化的层来编码输入
        for feature_name, feature_value in inputs.items():
            # 使用预定义的查找层和嵌入层
            lookup_layer = self.lookup_layers[feature_name]
            embedding_layer = self.embedding_layers[feature_name]
            encoded_feature = embedding_layer(lookup_layer(feature_value))
            encoded_features.append(encoded_feature)

            # 特征动态权重
        senet_output = self.senet_layer(encoded_features)  # [B, N, dim]
        senet_flatten_output = tf.keras.layers.Flatten()(senet_output)  # [B, N*dim]
        crossnet_output = self.crossnet_layer(senet_flatten_output)
        concat_output = tf.keras.layers.Concatenate()([senet_flatten_output, crossnet_output])
        dnn_output = self.dnn_layer(concat_output)
        # 最终输出
        logit = self.output_layer(dnn_output)
        return logit

    def get_config(self):
        # 调用基类的get_config方法（如果基类实现了get_config）
        config = super(QuantModel, self).get_config()
        # 添加QuantModel特有的配置信息
        config.update(
            {
                # 假设self.config是一个可序列化的字典，如果不是，你可能需要在这里适当地处理它
                "config": self.config
            }
        )
        return config
