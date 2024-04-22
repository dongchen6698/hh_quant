import tensorflow as tf
from ..layers import DnnLayer, BitWiseSeNet


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

        # 自定义ExpertPart
        self.experts = []
        for i in range(self.config.get("expert_nums", 6)):
            expert_part = tf.keras.Sequential(
                [
                    BitWiseSeNet(
                        reduction_ratio=self.config.get("reduction_ratio", 3),
                        l2_reg=self.config.get("l2_reg", 0.0),
                        seed=self.config.get("seed", 1024) + i,
                    ),
                    DnnLayer(
                        hidden_units=self.config.get("dnn_hidden_units", [64, 32]),
                        activation=self.config.get("dnn_activation", "relu"),
                        dropout_rate=self.config.get("dnn_dropout", 0.2),
                        use_bn=self.config.get("dnn_use_bn", True),
                        l2_reg=self.config.get("l2_reg", 0.0),
                        seed=self.config.get("seed", 1024) + i,
                    ),
                ]
            )
            self.experts.append(expert_part)

        # 自定义GatePart
        self.gates = []
        for i in range(self.config.get("task_nums", 2)):
            gate_part = tf.keras.layers.Dense(
                self.config.get("expert_nums", 6),
                activation=tf.nn.sigmoid,
            )
            self.gates.append(gate_part)

        # 自定义taskTowerPart
        self.task_towers = []
        for i in range(self.config.get("task_nums", 2)):
            task_tower = DnnLayer(
                hidden_units=self.config.get("dnn_hidden_units", [64, 32]),
                activation=self.config.get("dnn_activation", "relu"),
                dropout_rate=self.config.get("dnn_dropout", 0.2),
                use_bn=self.config.get("dnn_use_bn", True),
                l2_reg=self.config.get("l2_reg", 0.0),
                seed=self.config.get("seed", 1024) + i,
            )
            self.task_towers.append(task_tower)

        # 自定义taskOutputPart
        self.deep_outputs = [
            tf.keras.layers.Dense(3, activation=None, name=f"deep_output_cls"),
            tf.keras.layers.Dense(1, activation=None, name=f"deep_output_reg"),
        ]

        # 定义Wide层
        self.wide_outputs = [
            tf.keras.layers.Dense(3, activation=None, name="wide_output_cls"),
            tf.keras.layers.Dense(1, activation=None, name="wide_output_reg"),
        ]

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

        # Deep..........................................................................................
        output_logits = []
        deep_input = tf.concat([sparse_emb, dense_emb], axis=-1)
        expert_outputs = [expert(deep_input) for expert in self.experts]
        expert_output = tf.stack(expert_outputs, axis=1)  # [B, expert_nums, dim]
        for i in range(self.config.get("task_nums", 2)):
            # 构建Deep侧输出
            gate_output = self.gates[i](deep_input)
            gate_output = tf.expand_dims(gate_output, axis=-1)  # [B, dim, 1]
            deep_output = tf.multiply(gate_output, expert_output)  # [B, expert_nums, dim]
            deep_output = tf.keras.layers.Flatten()(deep_output)  # [B, expert_nums * dim]
            deep_output = self.task_towers[i](deep_output)  # [B, dim]
            deep_logit = self.deep_outputs[i](deep_output)
            # 构建Wide侧输出
            wide_logit = self.wide_outputs[i](deep_input)
            # 汇总最后输出
            output_logits.append(deep_logit + wide_logit)
        # Output........................................................................................
        return output_logits

    def get_config(self):
        config = super(QuantModel, self).get_config()
        config.update({"config": self.config})
        return config
