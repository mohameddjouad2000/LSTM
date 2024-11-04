# -*- coding: utf-8 -*-
"""last 31.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1kpeGNgftourPRcBfRljSqKg1K60ptEwU
"""

import numpy as np
import pandas as pd
import random
from google.colab import files
from sklearn.preprocessing import MinMaxScaler
from scipy.stats import pearsonr
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split

seed = 42
np.random.seed(seed)
random.seed(seed)
tf.random.set_seed(seed)


uploaded = files.upload()
file_name = list(uploaded.keys())[0]
data = pd.read_csv(file_name)

numeric_columns = data.select_dtypes(include=['float64', 'int64']).columns

data[numeric_columns] = data[numeric_columns].fillna(data[numeric_columns].mean())

features = data
target = data['FH.6000.[ENS] - Energy Signals.Momentary power consumption']

numeric_features = features.select_dtypes(include=[np.number])

weighted_features = numeric_features.copy()


for column in weighted_features.columns:
    if column != 'FH.6000.[ENS] - Energy Signals.Momentary power consumption':
        correlation, _ = pearsonr(weighted_features[column], target)
        weighted_features[column] *= correlation

feature_scaler = MinMaxScaler()
target_scaler = MinMaxScaler()
scaled_features = feature_scaler.fit_transform(weighted_features)
scaled_target = target_scaler.fit_transform(target.values.reshape(-1, 1))


scaled_features_df = pd.DataFrame(scaled_features, index=weighted_features.index, columns=weighted_features.columns)


scaled_features_df.head()

def create_sequences(features, target, sequence_length):
    xs, ys = [], []
    for i in range(len(features) - sequence_length):
        x = features[i:i + sequence_length]
        y = target[i + sequence_length]
        xs.append(x)
        ys.append(y)
    return np.array(xs), np.array(ys)
sequence_length = 50


X, y = create_sequences(scaled_features, scaled_target, sequence_length)

print(f'Input shape (X): {X.shape}')
print(f'Target shape (y): {y.shape}')

X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, shuffle=False)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, shuffle=False)

model = Sequential()
model.add(Input(shape=(X_train.shape[1], X_train.shape[2])))
model.add(LSTM(units=128, return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(units=100, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(units=1))
model.compile(optimizer='adam', loss='mean_squared_error')
model.summary()

history = model.fit(X_train, y_train,
                    epochs=10,
                    batch_size=64,
                    validation_data=(X_val, y_val))


plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss During Training')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend()
plt.show()

y_pred = model.predict(X_test)

y_test_rescaled = target_scaler.inverse_transform(y_test.reshape(-1, 1))
y_pred_rescaled = target_scaler.inverse_transform(y_pred)


mse = mean_squared_error(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mse)

print(f'Mean Squared Error: {mse}')
print(f'Mean Absolute Error (MAE): {mae}')
print(f'Root Mean Squared Error (RMSE): {rmse}')

plt.plot(y_test_rescaled, label='Actual Values')
plt.plot(y_pred_rescaled, label='Predicted Values')
plt.title('Actual vs Predicted Momentary Energy Consumption')
plt.ylabel('Energy Consumption')
plt.legend()
plt.show()

payload_weight = data['payload_weight']
fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(target, label='Momentary Power Consumption', color='blue')
ax1.set_xlabel('Sample Index')
ax1.set_ylabel('Momentary Power Consumption', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.set_xticks(np.arange(0, len(target), 5000))
ax1.set_yticks(np.arange(0, max(target) + 100, 100))

ax2 = ax1.twinx()
ax2.plot(payload_weight, label='Payload Weight', color='red')
ax2.set_ylabel('Payload Weight', color='red')
ax2.tick_params(axis='y', labelcolor='red')
ax1.grid(visible=True, which='both', color='grey', linestyle='--', linewidth=0.5)
fig.suptitle('Momentary Power Consumption and Payload Weight Over Samples')
ax1.legend(loc='upper right')
ax2.legend(loc='upper right', bbox_to_anchor=(1, 0.95))

plt.show()

import seaborn as sns
speed_column = 'FH.6000.[NNS] - Natural Navigation Signals.Speed'
energy_column = 'FH.6000.[ENS] - Energy Signals.Momentary energy consumption'
weight_column = 'payload_weight'
data_sampled = data.iloc[::1].copy()
data_sampled['Absolute_Speed'] = data_sampled[speed_column].abs()
weight_bins = [0, 200, 400, float("inf")]
weight_labels = ['Low', 'Medium', 'High']
data_sampled['Weight Range'] = pd.cut(data_sampled[weight_column], bins=weight_bins, labels=weight_labels)
plt.figure(figsize=(12, 8))
sns.scatterplot(data=data_sampled, x='Absolute_Speed', y=energy_column, hue='Weight Range', palette='Set2', alpha=0.7)
plt.title('Absolute Speed vs. Momentary Energy Consumption by Weight Load')
plt.xlabel('Absolute Speed')
plt.ylabel('Momentary Energy Consumption')
plt.legend(title='Weight Range')
plt.grid(True)
plt.show()

data['isoTimestamp'] = pd.to_datetime(data['isoTimestamp'])
data = data.drop_duplicates(subset='isoTimestamp')
data_subset = data.iloc[:1250]
actual_speed_col = 'FH.6000.[G1LDS] GROUP 1 - LEFT DRIVE SIGNALS.ActualSpeed_L'

data_subset['Acceleration'] = np.where(
    (data_subset[actual_speed_col].shift(-1) > data_subset[actual_speed_col]),
    data_subset[actual_speed_col].shift(-1) - data_subset[actual_speed_col],
    np.where(
        (data_subset[actual_speed_col].shift(-1) < data_subset[actual_speed_col]),
        np.where(
            (data_subset[actual_speed_col].shift(-1) < 0) & (data_subset[actual_speed_col] < 0),
            abs(data_subset[actual_speed_col].shift(-1)) - abs(data_subset[actual_speed_col]),
            data_subset[actual_speed_col].shift(-1) - data_subset[actual_speed_col]
        ),
        0
    )
)
data_subset = data_subset.dropna(subset=['Acceleration'])
fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(data_subset['isoTimestamp'], data_subset['Acceleration'], color='blue', linestyle='-', label='Acceleration/Deceleration')
ax2 = ax1.twinx()
power_consumption_col = 'FH.6000.[ENS] - Energy Signals.Momentary power consumption'
ax2.plot(data_subset['isoTimestamp'], data_subset[power_consumption_col], color='red', label='Momentary Power Consumption', linestyle='-')
plt.title('Acceleration/Deceleration and Momentary Power Consumption for the First 1250 Rows')
ax1.set_xlabel('Timestamp')
ax1.set_ylabel('Acceleration (blue)')
ax2.set_ylabel('Power Consumption (red)')
plt.xticks(rotation=45)
ax1.legend(loc='upper left')
ax2.legend(loc='upper right')
plt.grid()
plt.tight_layout()
plt.show()