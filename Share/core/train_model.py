import sys
sys.path.append('../')

import warnings
warnings.filterwarnings("ignore")
import os
import pandas as pd
import numpy as np
import akshare as ak
import sqlite3
import matplotlib.pyplot as plt
# %matplotlib inline

from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
from database.downloader.downloader_base import DownloaderBase
import database.database_config as db_config
from models.multi_task.model_mmoe import QuantModel
pd.options.display.max_rows=None
pd.options.display.max_columns=None

import tensorflow as tf
from get_features import init_database

# 只使用CPU进行训练
tf.config.set_visible_devices([], 'GPU')

# 打印Tensorflow版本
print(f"Tensorflow Version: {tf.__version__}")

# 检查是否有可用的GPU设备
if tf.test.is_built_with_cuda():
    print("TensorFlow GPU version is installed")
else:
    print("TensorFlow CPU version is installed")

# 检查TensorFlow是否能够访问GPU
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print("GPU devices available:", gpus)
else:
    print("No GPU devices found. Running on CPU.")

# !nvidia-smi

def get_rolling_data_period(backtest_start_date, backtest_duration=5, train_period=6, val_period=0.5, test_period=0.5):
    """
    Args:
        backtest_start_date (_type_): _description_
        backtest_duration (int, optional): _description_. Defaults to 5.
        train_period (int, optional): _description_. Defaults to 6.
        val_period (float, optional): _description_. Defaults to 0.5.
        test_period (float, optional): _description_. Defaults to 0.5.
    Returns:
        result: _description_
    """
    backtest_start_date = datetime.strptime(backtest_start_date, '%Y%m%d')
    backtest_end_date = backtest_start_date + relativedelta(years=backtest_duration) # 回测5年数据
    train_period = relativedelta(years=train_period) # 使用6年的训练数据
    val_period = relativedelta(months=(12 * val_period)) # 使用半年的验证数据
    test_period = relativedelta(months=(12 * test_period)) # 使用半年的测试数据(半年模型一更新)

    result = []
    rolling_flag = True
    bench_date = backtest_start_date
    while rolling_flag:
        if bench_date < backtest_end_date:
            test_start, test_end = bench_date, (bench_date + test_period - relativedelta(days=1))
            val_start, val_end = (test_start - relativedelta(days=1) - val_period), (test_start - relativedelta(days=1))
            train_start, train_end =(val_start - relativedelta(days=1) - train_period), (val_start - relativedelta(days=1))
            result.append({
                "train": [train_start.strftime("%Y%m%d"), train_end.strftime("%Y%m%d")],
                "val": [val_start.strftime("%Y%m%d"), val_end.strftime("%Y%m%d")],
                "test": [test_start.strftime("%Y%m%d"), test_end.strftime("%Y%m%d")]
            })
            bench_date += test_period
        else:
            rolling_flag = False 
    return result

def extract_train_val_data(df, train_start_date, train_end_date, val_start_date, val_end_date, test_start_date, test_end_date):
    train_start_date = pd.to_datetime(train_start_date)
    train_end_date = pd.to_datetime(train_end_date)
    val_start_date = pd.to_datetime(val_start_date)
    val_end_date = pd.to_datetime(val_end_date)
    test_start_date = pd.to_datetime(test_start_date)
    test_end_date = pd.to_datetime(test_end_date)

    train_data = df[(pd.to_datetime(df['datetime']) >= train_start_date) & (pd.to_datetime(df['datetime']) <= train_end_date)]
    val_data = df[(pd.to_datetime(df['datetime']) >= val_start_date) & (pd.to_datetime(df['datetime']) <= val_end_date)]
    test_data = df[(pd.to_datetime(df['datetime']) >= test_start_date) & (pd.to_datetime(df['datetime']) <= test_end_date)]

    print(f"train_data_size: {train_data.shape}")
    print(f"validation_data_size: {val_data.shape}")
    print(f"test_data_size: {test_data.shape}")
    return train_data, val_data, test_data

def df_to_dataset(dataframe, feature_cols, label_cols, shuffle=True, batch_size=32):
    features = dataframe[feature_cols]
    labels = tuple([dataframe[col] for col in label_cols])
    # labels = dataframe[label_cols]
    ds = tf.data.Dataset.from_tensor_slices((dict(features), labels))
    if shuffle:
        ds = ds.shuffle(buffer_size=min(len(features), 10000))
    ds = ds.cache().batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return ds



from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import MinMaxScaler, StandardScaler

class CustomPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, outlier_process=False, minmax_scale=True, standard_scale=False):
        # 配置异常值处理
        self.outlier_process = outlier_process
        self.outlier_params = {}
        # 配置MinMaxScaler
        self.minmax_scale = minmax_scale
        # 配置StandardScaler
        self.standard_scale = standard_scale
        
    def _fit_outlier_cap(self, X):
        # 计算并存储异常值处理参数
        Q1, Q3 = np.nanpercentile(X, [25, 75], axis=0)
        IQR = Q3 - Q1
        self.outlier_params['outliers_lower_bounds_'] = Q1 - 1.5 * IQR
        self.outlier_params['outliers_upper_bounds_'] = Q3 + 1.5 * IQR
        
    def _transform_outlier_cap(self, X):
        # 根据存储的参数应用异常值限制
        return np.clip(X, self.outlier_params['outliers_lower_bounds_'], self.outlier_params['outliers_upper_bounds_'])
    
    def fit(self, X, y=None):
        if self.outlier_process:
            self._fit_outlier_cap(X)
        # 初始化归一化和标准化转换器
        self.scalers_ = []
        if self.minmax_scale:
            minmax_scaler = MinMaxScaler()
            minmax_scaler.fit(X)
            self.scalers_.append(minmax_scaler)
        if self.standard_scale:
            standard_scaler = StandardScaler()
            standard_scaler.fit(X)
            self.scalers_.append(standard_scaler)
        return self
    
    def transform(self, X, y=None):
        if self.outlier_process:
            X = self._transform_outlier_cap(X)
        # 应用归一化和标准化转换
        for scaler in self.scalers_:
            X = scaler.transform(X)
        return X



def prepare_train_features(proprocessor,batch_size=1024):

    # 相关配置
    rolling_flag = False
    benchmark = '000016'
    feature_config = {
        "target_features": ['label', 'return'],
        "numeric_features": ['turnover_rate', 'pe_ttm', 'ps_ttm', 'pcf_ncf_ttm', 'pb_mrq', 'KMID', 'KLEN', 'KMID2', 'KUP', 'KUP2', 'KLOW', 'KLOW2', 'KSFT', 'KSFT2', 'OPEN0', 'OPEN1', 'OPEN2', 'OPEN3', 'OPEN4', 'HIGH0', 'HIGH1', 'HIGH2', 'HIGH3', 'HIGH4', 'LOW0', 'LOW1', 'LOW2', 'LOW3', 'LOW4', 'CLOSE1', 'CLOSE2', 'CLOSE3', 'CLOSE4', 'VOLUME1', 'VOLUME2', 'VOLUME3', 'VOLUME4', 'ROC5', 'ROC10', 'ROC20', 'ROC30', 'ROC60', 'MAX5', 'MAX10', 'MAX20', 'MAX30', 'MAX60', 'MIN5', 'MIN10', 'MIN20', 'MIN30', 'MIN60', 'MA5', 'MA10', 'MA20', 'MA30', 'MA60', 'STD5', 'STD10', 'STD20', 'STD30', 'STD60', 'BETA5', 'BETA10', 'BETA20', 'BETA30', 'BETA60', 'RSQR5', 'RSQR10', 'RSQR20', 'RSQR30', 'RSQR60', 'RESI5', 'RESI10', 'RESI20', 'RESI30', 'RESI60', 'QTLU5', 'QTLU10', 'QTLU20', 'QTLU30', 'QTLU60', 'QTLD5', 'QTLD10', 'QTLD20', 'QTLD30', 'QTLD60', 'TSRANK5', 'TSRANK10', 'TSRANK20', 'TSRANK30', 'TSRANK60', 'RSV5', 'RSV10', 'RSV20', 'RSV30', 'RSV60', 'IMAX5', 'IMAX10', 'IMAX20', 'IMAX30', 'IMAX60', 'IMIN5', 'IMIN10', 'IMIN20', 'IMIN30', 'IMIN60', 'IMXD5', 'IMXD10', 'IMXD20', 'IMXD30', 'IMXD60', 'CORR5', 'CORR10', 'CORR20', 'CORR30', 'CORR60', 'CORD5', 'CORD10', 'CORD20', 'CORD30', 'CORD60', 'CNTP5', 'CNTP10', 'CNTP20', 'CNTP30', 'CNTP60', 'CNTN5', 'CNTN10', 'CNTN20', 'CNTN30', 'CNTN60', 'CNTD5', 'CNTD10', 'CNTD20', 'CNTD30', 'CNTD60', 'SUMP5', 'SUMP10', 'SUMP20', 'SUMP30', 'SUMP60', 'SUMN5', 'SUMN10', 'SUMN20', 'SUMN30', 'SUMN60', 'SUMD5', 'SUMD10', 'SUMD20', 'SUMD30', 'SUMD60', 'VMA5', 'VMA10', 'VMA20', 'VMA30', 'VMA60', 'VSTD5', 'VSTD10', 'VSTD20', 'VSTD30', 'VSTD60', 'WVMA5', 'WVMA10', 'WVMA20', 'WVMA30', 'WVMA60', 'VSUMP5', 'VSUMP10', 'VSUMP20', 'VSUMP30', 'VSUMP60', 'VSUMN5', 'VSUMN10', 'VSUMN20', 'VSUMN30', 'VSUMN60', 'VSUMD5', 'VSUMD10', 'VSUMD20', 'VSUMD30', 'VSUMD60'],
        "integer_categorical_features": ['month'],
        "string_categorical_features": ['industry', 'season'],
    }
    batch_size = batch_size

    # 是否开启滚动训练&回测
    if rolling_flag:
        print("开启滚动回测...")
        backtest_period = get_rolling_data_period(
            backtest_start_date='20200101', # 回测开始日期
            backtest_duration=4, # 一共回测多久的数据（单位：年）
            train_period=6, # 使用过去多久的时间进行训练（单位：年）
            val_period=1, # 验证数据周期（单位：年）
            test_period=1, # 测试数据周期（单位：年）
        )
    else:
        print("关闭滚动回测...")
        backtest_period = [
            {
                'train': ['20120101', '20171231'],
                'val': ['20180101', '20181231'],
                'test': ['20190101', '20231231']
            }
        ]

    print(f"rolling_flag is :{rolling_flag}, backtest_period is :",backtest_period)

    date_period_params = backtest_period[0]
    print(date_period_params)
    train_start_date, train_end_date = date_period_params['train']
    val_start_date, val_end_date = date_period_params['val']
    test_start_date, test_end_date = date_period_params['test']
    # 获取全区间数据
    print("开始加载原始数据...")
    df = proprocessor._process_all_stock(code_type=benchmark, start_date=train_start_date, end_date=test_end_date)
    # 抽取训练验证数据
    print("开始拆分训练、验证、测试集合...")
    train_data, val_data, test_data = extract_train_val_data(df, *[train_start_date, train_end_date, val_start_date, val_end_date, test_start_date, test_end_date])
    # 计算类别权重
    print("开始计算类别权重...")
    value_count = train_data['label'].value_counts()
    print(value_count)
    total_count = train_data['label'].count()
    class_weights = ((1 / value_count) * (total_count / 2.0)).to_dict()
    print(f"class_weights is : {class_weights}")

    # 从data中抽取相关特征数据
    print("开始抽取特征数据...")
    feature_columns = feature_config.get('numeric_features', []) + feature_config.get('integer_categorical_features', []) + feature_config.get('string_categorical_features', [])
    label_columns = feature_config.get('target_features', [])
    full_feature_columns = feature_columns + label_columns
    train_df, val_df, test_df = train_data[full_feature_columns], val_data[full_feature_columns], test_data[full_feature_columns]
    # 对相关特征进行特征工程
    print("开始特征工程处理...")
    feature_preprocess_pipeline = CustomPreprocessor()
    numeric_feature_columns = feature_config.get('numeric_features', [])
    train_df[numeric_feature_columns] = feature_preprocess_pipeline.fit_transform(train_df[numeric_feature_columns])
    val_df[numeric_feature_columns] = feature_preprocess_pipeline.transform(val_df[numeric_feature_columns])
    test_df[numeric_feature_columns] = feature_preprocess_pipeline.transform(test_df[numeric_feature_columns])
    # 转换为tensorflow所使用的dataset
    print("开始将DataFrame转换为DataSet...")
    train_ds = df_to_dataset(train_df, feature_columns, label_columns, shuffle=True, batch_size=batch_size)
    val_ds = df_to_dataset(val_df, feature_columns, label_columns, shuffle=False, batch_size=batch_size)
    test_ds = df_to_dataset(test_df, feature_columns, label_columns, shuffle=False, batch_size=batch_size) 

    
    numeric_features_with_boundaries = {k: pd.qcut(train_df[k], q=20, retbins=True, duplicates='drop')[1].tolist() for k in feature_config.get('numeric_features', [])}
    integer_categorical_features_with_vocab = {k: list(train_df[k].unique()) for k in feature_config.get('integer_categorical_features', [])}
    string_categorical_features_with_vocab = {k: list(train_df[k].unique()) for k in feature_config.get('string_categorical_features', [])}
    model_params = {
        "numeric_features_with_boundaries": numeric_features_with_boundaries,
        "integer_categorical_features_with_vocab":integer_categorical_features_with_vocab,
        "string_categorical_features_with_vocab": string_categorical_features_with_vocab,
    }

    return (train_df, val_df, test_df),(train_ds,val_ds,test_ds),model_params,class_weights



def train(train_ds,val_ds,test_ds,**kwargs):
    # 准备模型训练
    print("开始模型初始化 & 训练...")
    # 自定义模型
    batch_size =  kwargs.get("batch_size",1024)
    class_weights = kwargs.get("class_weights")

    model_params = kwargs.get("model_params",{})
    model_config = {
            "seed": 1024,
            "feature_use_embedding": True,
            "feature_embedding_dims": 4,
            # "numeric_features_with_boundaries": "",
            # "integer_categorical_features_with_vocab":"",
            # "string_categorical_features_with_vocab": "",
    }
    model_config.update(model_params)
    print(f"cur model config is :{model_config}")
    model = QuantModel(config=model_config)

    # 自定义优化器
    initial_learning_rate = 5e-4
    lr_schedule = tf.keras.optimizers.schedules.InverseTimeDecay(
        initial_learning_rate, decay_steps=(len(train_ds) // batch_size) * 10, decay_rate=1, staircase=False
    )
    optimizer = tf.keras.optimizers.Adam(lr_schedule)

    # 自定义损失函数
    cls_loss_object = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True) # 分类损失
    reg_loss_object = tf.keras.losses.MeanAbsoluteError() # 回归损失
    # 自定义指标Loss
    train_loss = tf.keras.metrics.Mean(name="train_loss")
    val_loss = tf.keras.metrics.Mean(name="val_loss")
    # 自定义指标metrics
    train_cls_metric = tf.keras.metrics.SparseCategoricalAccuracy(name="train_accuracy")
    train_reg_metric = tf.keras.metrics.MeanAbsoluteError(name="train_mae")
    val_cls_metric = tf.keras.metrics.SparseCategoricalAccuracy(name="val_accuracy")
    val_reg_metric = tf.keras.metrics.MeanAbsoluteError(name="val_mae")

    # 自定义训练步骤
    @tf.function
    def train_step(inputs, labels):
        with tf.GradientTape() as tape:
            predictions = model(inputs, training=True)
            cls_label, reg_label = labels
            cls_pred, reg_pred = predictions
            cls_sample_weights = tf.gather(
                tf.constant([class_weights[ind] for ind in sorted(class_weights.keys())], dtype=tf.float32),
                tf.cast(cls_label, dtype=tf.int32)
            )
            cls_loss = cls_loss_object(cls_label, cls_pred, sample_weight=cls_sample_weights)
            reg_loss = reg_loss_object(reg_label, reg_pred)
            loss = cls_loss + reg_loss
        gradients = tape.gradient(loss, model.trainable_variables)
        optimizer.apply_gradients(zip(gradients, model.trainable_variables))
        train_loss(loss)
        train_cls_metric(cls_label, cls_pred)
        train_reg_metric(reg_label, reg_pred)


    # 自定义验证步骤
    @tf.function
    def val_step(inputs, labels):
        predictions = model(inputs, training=False)
        cls_label, reg_label = labels
        cls_pred, reg_pred = predictions
        cls_loss = cls_loss_object(cls_label, cls_pred)
        reg_loss = reg_loss_object(reg_label, reg_pred)
        loss = cls_loss + reg_loss
        val_loss(loss)
        val_cls_metric(cls_label, cls_pred)
        val_reg_metric(reg_label, reg_pred)

    
    # 设定早停参数
    patience = 10
    best_val_loss = float('inf')
    patience_counter = 0
    best_weights=None
    restore_best_weights=True

    EPOCHS = 500
    for epoch in range(EPOCHS):
        # 重新初始化Epoch内的参数
        train_loss.reset_states()
        val_loss.reset_states()
        train_cls_metric.reset_states()
        train_reg_metric.reset_states()
        val_cls_metric.reset_states()
        val_reg_metric.reset_states()

        # 训练逻辑
        for train_inputs, train_labels in tqdm(train_ds, desc="Training..."):
            train_step(train_inputs, train_labels)

        # 验证逻辑
        for val_inputs, val_labels in tqdm(val_ds, desc='Validatioin...'):
            val_step(val_inputs, val_labels)

        # EarlyStoping逻辑
        current_val_loss = val_loss.result()
        if current_val_loss <= best_val_loss:
            best_val_loss = current_val_loss
            patience_counter = 0
            # 可以选择在这里保存模型
            best_weights = model.get_weights()
            # model.save('path_to_my_model.h5')
        else:  # 如果不是，则耐心计数器加1
            patience_counter += 1
        # 如果耐心计数器超出设定的耐心值，则停止训练
        if patience_counter > patience:
            print(f'Early stopping at epoch {epoch + 1}')
            if restore_best_weights and best_weights is not None:
                # 恢复最佳权重
                print('Restoring model weights from the end of the best epoch.')
                model.set_weights(best_weights)
            break
        print(
        f"Epoch {epoch + 1}, "
        f"loss: {train_loss.result():.4f}, "
        f"accuracy: {train_cls_metric.result() * 100:.4f}, "
        f"mse: {train_reg_metric.result():.4f}, "
        f"val_loss: {val_loss.result():.4f}, "
        f"val_accuracy: {val_cls_metric.result() * 100:.4f}, "
        f"val_mse: {val_reg_metric.result():.4f}, "
    )
        
    return model
        


if __name__ == "__main__":
    proprocessor  = init_database()
    batch_size = 256
    (train_df, val_df, test_df),(train_ds,val_ds,test_ds),model_params,class_weights = prepare_train_features(proprocessor,batch_size=batch_size)
    model = train(train_ds,val_ds,test_ds,model_params= model_params,class_weights= class_weights,batch_size=batch_size)
    # test数据处理
    test_cls_result, test_reg_result = model.predict(test_ds)

    from sklearn.metrics import classification_report
    test_true = test_df['label']
    test_pred = np.argmax(tf.nn.softmax(test_cls_result), axis=-1)
    print(classification_report(test_true, test_pred))

    ## 保存模型：
    model.save_weights("/hy-tmp/Quant/hh_quant/Share/outputs")