# optimizer = tf.keras.optimizers.legacy.Adam(learning_rate=5e-3) # for Mac M1/M2
optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3)
loss_fn_reg = tf.keras.losses.MeanSquaredError()  # 回归任务的损失函数
loss_fn_cls = tf.keras.losses.BinaryCrossentropy(from_logits=True)  # 分类任务的损失函数
num_epochs = 20
best_val_loss = float("inf")
patience = 5
wait = 0

# 定义epoch相关指标 -- train
train_total_loss_metric = tf.keras.metrics.Mean(name="train_total_loss")
train_reg_loss_metric = tf.keras.metrics.Mean(name="train_reg_loss")
train_cls_loss_metric = tf.keras.metrics.Mean(name="train_cls_loss")
# 定义epoch相关指标 -- validation
val_total_loss_metric = tf.keras.metrics.Mean(name="val_total_loss")
val_reg_loss_metric = tf.keras.metrics.Mean(name="val_reg_loss")
val_cls_loss_metric = tf.keras.metrics.Mean(name="val_cls_loss")

for epoch in range(num_epochs):
    print(f"Epoch {epoch+1}/{num_epochs}")

    # Reset the metrics at the start of the next epoch
    train_total_loss_metric.reset_states()
    train_reg_loss_metric.reset_states()
    train_cls_loss_metric.reset_states()

    # Training loop - iterate over the training dataset
    for step, (x_batch_train, y_batch_train) in enumerate(tqdm(train_ds, desc="Training...")):
        with tf.GradientTape() as tape:
            logits_list = model(x_batch_train, training=True)  # 前向传播
            reg_loss = loss_fn_reg(y_batch_train[0], logits_list[0])  # 计算回归任务的损失
            cls_loss = loss_fn_cls(y_batch_train[1], logits_list[1])  # 计算分类任务的损失
            # 应用类别权重
            cls_weights = tf.constant([class_weight[int(cls)] for cls in y_batch_train[1]], dtype=tf.float32)
            cls_loss_weighted = tf.reduce_mean(cls_loss * cls_weights)  # 根据权重调整分类损失
            # 汇总loss
            total_loss = reg_loss + cls_loss_weighted  # 根据任务权重合并损失
            # 记录loss
            train_total_loss_metric.update_state(total_loss)
            train_reg_loss_metric.update_state(reg_loss)
            train_cls_loss_metric.update_state(cls_loss_weighted)

        grads = tape.gradient(total_loss, model.trainable_weights)  # 反向传播，计算梯度
        optimizer.apply_gradients(zip(grads, model.trainable_weights))  # 更新模型权重
    print(
        f"Training one epoch at step {step} -- trainLoss:{train_total_loss_metric.result().numpy()}, regLoss{train_reg_loss_metric.result().numpy()}, clsLoss{train_cls_loss_metric.result().numpy()}"
    )

    # Validation loop - iterate over the validation dataset
    val_total_loss_metric.reset_states()
    val_reg_loss_metric.reset_states()
    val_cls_loss_metric.reset_states()
    val_loss = 0
    val_reg_loss = 0
    val_cls_loss = 0
    for x_batch_val, y_batch_val in tqdm(val_ds, desc="Validation..."):
        val_logits_list = model(x_batch_val, training=False)
        val_reg_loss += loss_fn_reg(y_batch_val[0], val_logits_list[0])
        val_cls_loss += loss_fn_cls(y_batch_val[1], val_logits_list[1])
        val_loss += val_reg_loss + val_cls_loss

    val_loss /= len(val_ds)
    val_reg_loss /= len(val_ds)
    val_cls_loss /= len(val_ds)

    val_total_loss_metric.update_state(val_loss)
    val_reg_loss_metric.update_state(val_reg_loss)
    val_cls_loss_metric.update_state(val_cls_loss)
    print(
        f"Validation one epoch at step {step} -- trainLoss:{val_total_loss_metric.result().numpy()}, regLoss{val_reg_loss_metric.result().numpy()}, clsLoss{val_cls_loss_metric.result().numpy()}"
    )

    # Early Stoping and saving best weights
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        wait = 0
        model.save("best_model", save_format="tf")  # 保存最优权重
    else:
        wait += 1
        if wait >= patience:
            print("Early stopping...")
            break

# Training is complete - load best weights
model = tf.keras.models.load_model("best_model")
