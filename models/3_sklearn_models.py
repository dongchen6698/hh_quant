from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

# 1. 加载数据集
iris = load_iris()
X, y = iris.data, iris.target

# 2. 数据预处理（这一步在这个例子中是可选的，因为决策树不一定需要标准化特征）
# 但对于很多其他模型（如SVM、逻辑回归等）来说，这是推荐的步骤。
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 3. 选择一个模型
model = DecisionTreeClassifier()

# 4. 划分数据集为训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# 5. 训练模型
model.fit(X_train, y_train)

# 6. 评估模型性能
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy:.2f}")

# 7. 调整模型参数（如果需要，通过交叉验证如GridSearchCV）
# 8. 使用模型进行预测（可用于新的、未见过的数据）
