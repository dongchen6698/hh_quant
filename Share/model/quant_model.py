from __future__ import division, print_function
import os
import sys

cur_path = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.abspath(os.path.join(cur_path, "..")))
sys.path.append(os.path.abspath(os.path.join(cur_path, "../..")))

import tensorflow as tf
from .layers import SeNetLayer, DnnLayer, FMLayer


class QuantModel(tf.keras.Model):
    def __init__(self, config, **kwargs):
        super(QuantModel, self).__init__(**kwargs)
        self.config = config

        # 添加属性来存储预定义的层
        # self.wide_layers = {}
        self.lookup_layers = {}
        self.embedding_layers = {}

        # # 创建Wide侧相关的one_hot特征
        # for feature_name, boundaries in self.config.get("numeric_features_with_boundaries").items():
        #     self.wide_layers[feature_name] = tf.keras.layers.Discretization(bin_boundaries=boundaries, output_mode="one_hot", name=f"{feature_name}_lookup")

        # # 创建连续特征的离散化层和嵌入层
        # for feature_name, boundaries in self.config.get("numeric_features_with_boundaries").items():
        #     self.lookup_layers[feature_name] = tf.keras.layers.Discretization(bin_boundaries=boundaries, output_mode="int", name=f"{feature_name}_lookup")
        #     self.embedding_layers[feature_name] = tf.keras.layers.Embedding(
        #         input_dim=len(boundaries) + 1, output_dim=self.config.get("feature_embedding_dims", 6), name=f"{feature_name}_embedding"
        #     )
        # 创建连续特征（分桶）的查找层和嵌入层
        for feature_name, vocab in self.config.get("numeric_categorical_features_with_vocab").items():
            self.lookup_layers[feature_name] = tf.keras.layers.IntegerLookup(vocabulary=vocab, name=f"{feature_name}_lookup")
            self.embedding_layers[feature_name] = tf.keras.layers.Embedding(
                input_dim=len(vocab) + 1, output_dim=self.config.get("feature_embedding_dims", 6), name=f"{feature_name}_embedding"
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
            l2_reg=self.config.get("l2_reg", 0.0),
            seed=self.config.get("seed", 1024),
        )
        self.cross_layer = FMLayer()
        self.dnn_layer = DnnLayer(
            hidden_units=self.config.get("dnn_hidden_units", [64, 32]),
            activation=self.config.get("dnn_activation", "relu"),
            dropout_rate=self.config.get("dnn_dropout", 0.2),
            use_bn=self.config.get("dnn_use_bn", True),
            l2_reg=self.config.get("l2_reg", 0.0),
            seed=self.config.get("seed", 1024),
        )
        # self.wide_output_layer = tf.keras.layers.Dense(1, activation=None)
        self.deep_output_layer = tf.keras.layers.Dense(1, activation=None)
        self.cross_output_layer = tf.keras.layers.Dense(1, activation=None)

    def call(self, inputs, training=False):
        if not isinstance(inputs, dict):
            raise ValueError("The inputs to the model should be a dictionary where keys are feature names.")
        # ==========================================================================================
        # 处理Wide侧特征
        # wide_features = []
        # for feature_name, feature_value in inputs.items():
        #     if feature_name in self.wide_layers:
        #         wide_features.append(self.wide_layers[feature_name](feature_value))
        # wide_output = tf.keras.layers.Concatenate()(wide_features)
        # wide_logit = self.wide_output_layer(wide_output)
        # ==========================================================================================
        # 处理Deep侧特征 - 首先使用seNet进行特征权重调整
        deep_features = []
        for feature_name, feature_value in inputs.items():
            lookup_layer = self.lookup_layers[feature_name]
            embedding_layer = self.embedding_layers[feature_name]
            encoded_feature = embedding_layer(lookup_layer(feature_value))
            deep_features.append(encoded_feature)
        deep_input = tf.stack(deep_features, axis=1)
        deep_input = self.senet_layer(deep_input)
        # ..........................................................................................
        # 处理Deep侧DNN特征
        dnn_output = tf.keras.layers.Flatten()(deep_input)
        dnn_output = self.dnn_layer(dnn_output)
        dnn_logit = self.deep_output_layer(dnn_output)
        # ..........................................................................................

        # ==========================================================================================
        # 处理Deep侧Cross特征
        cross_output = self.cross_layer(deep_input)  # [B, cinSize]
        cross_logit = self.cross_output_layer(cross_output)
        # ==========================================================================================
        # 最终输出
        final_logit = dnn_logit + cross_logit
        return final_logit

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
