# -*- coding: utf-8 -*-
"""Skin_cancer_multiclass.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/13CzkxqeC6M9NbSutIvEmfZdnMfrpQ4C_

# Requirements
"""

!pip uninstall tensorflow -q -y

!pip install tensorflow==2.9.0

import tensorflow as tf
print(tf.__version__)

"""# Load Modules"""

import requests
from google.colab import drive
import os
import shutil
import zipfile
import pandas as pd
import cv2
import numpy as np
import tensorflow as tf

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense
from tensorflow.keras.models import Model
from sklearn.utils import class_weight
from PIL import Image
from tqdm.notebook import tqdm

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from tensorflow.keras.applications.efficientnet import EfficientNetB0, preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Flatten, Input, Concatenate

from tensorflow.keras.layers import Flatten
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.regularizers import l2

from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, roc_curve, auc
import seaborn as sns
import matplotlib.pyplot as plt

from google.colab import drive
drive.mount('/content/drive')

"""# Load Dataset"""

# Define the paths to the destination folders for extraction
extracted_folder1 = '/content/drive/MyDrive/Skin Cancer/images/imgs_part_1'
extracted_folder2 = '/content/drive/MyDrive/Skin Cancer/images/imgs_part_2'
extracted_folder3 = '/content/drive/MyDrive/Skin Cancer/images/imgs_part_3'

# Define the path to the existing combined dataset folder
combined_dataset_folder = '/content/drive/My Drive/Skin Cancer/mendely'
# Specify the path to the pickle file

# # Only Run Once
# # Function to copy the contents of one folder to another
# def copy_folder_contents(source_folder, destination_folder):
#     for item in os.listdir(source_folder):
#         source_item = os.path.join(source_folder, item)
#         destination_item = os.path.join(destination_folder, item)
#         if os.path.isdir(source_item):
#             shutil.copytree(source_item, destination_item)
#         else:
#             shutil.copy2(source_item, destination_item)

# # Copy the contents of the first dataset folder to the combined dataset folder
# copy_folder_contents(extracted_folder1, combined_dataset_folder)

# # Copy the contents of the second dataset folder to the combined dataset folder
# copy_folder_contents(extracted_folder2, combined_dataset_folder)

# # Copy the contents of the second dataset folder to the combined dataset folder
# copy_folder_contents(extracted_folder3, combined_dataset_folder)

# Commented out IPython magic to ensure Python compatibility.
#path that contains folder you want to copy
# %cd /content/drive/My Drive/Skin Cancer/
# %cp -r mendely /content/mendely/
# %cd /content/

combined_dataset_folder = '/content/mendely'

# Function to count the number of images in a folder
def count_images_in_folder(folder_path):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    image_count = 0

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            _, extension = os.path.splitext(item_path)
            if extension.lower() in image_extensions:
                image_count += 1

    return image_count

# Count the number of images in the combined dataset folder
total_images = count_images_in_folder(combined_dataset_folder)
print("Total number of images in the 'combined_dataset' folder:", total_images)

# Load the dataset
metadata = pd.read_csv('metadata.csv')

"""# Data Preprocessing"""

# checking missing values
metadata.isna().sum()

# Checking Duplicates
duplicate_ids = metadata[metadata.duplicated(subset='patient_id')]
print(f"There are {duplicate_ids.shape[0]} duplicate patient ID's in the dataframe.")

# Removing Duplicates
metadata = metadata.drop_duplicates(subset='patient_id', keep='first')
metadata = metadata.reset_index(drop=True)

# Checking columns with UNK value
columns_with_unk = []

for column in metadata.columns:
    if 'UNK' in metadata[column].values:
        columns_with_unk.append(column)

print("Columns with 'UNK' values:", columns_with_unk)
# Replaocing UNK with False
metadata.replace('UNK', 'False', inplace=True)

# Fill missing values in 'skin_cancer_history' with the mode
metadata['skin_cancer_history'] = metadata['skin_cancer_history'].fillna(metadata['skin_cancer_history'].mode()[0])

# Fill missing values in 'diameter_1' and 'diameter_2' with the mean
metadata['diameter_1'] = metadata['diameter_1'].fillna(metadata['diameter_1'].mean())
metadata['diameter_2'] = metadata['diameter_2'].fillna(metadata['diameter_2'].mean())

metadata.head(5)

"""# EDA"""

df = metadata

sns.distplot(df['age'], kde=True)
plt.title('Age Distribution of Patients')
plt.show()

sns.pairplot(df[['age', 'diameter_1', 'diameter_2']].dropna())  # dropna to handle missing values
plt.show()

plt.figure(figsize=(15, 7))
sns.countplot(data=df, x='diagnostic', hue='bleed')
plt.title('Distribution of Diagnostic based on Bleed feature')
plt.xlabel('Diagnostic')
plt.ylabel('Count')
plt.xticks(rotation=45)
plt.show()

# Group the data by 'diagnostic' and 'hurt' columns and count the occurrences
grouped_data = metadata.groupby(['diagnostic', 'hurt']).size().reset_index(name='count')

# Create a bar plot
plt.figure(figsize=(12, 6))
sns.barplot(data=grouped_data, x='diagnostic', y='count', hue='hurt')
plt.title('Count of "Hurt" by Diagnostic')
plt.ylabel('Count')
plt.xlabel('Diagnostic')
plt.show()

# Group the data by 'diagnostic' and 'region' columns and count the occurrences
grouped_data = metadata.groupby(['diagnostic', 'region']).size().reset_index(name='count')

# Create a bar plot
plt.figure(figsize=(12, 6))
sns.barplot(data=grouped_data, x='diagnostic', y='count', hue='region')
plt.title('Count of "Region" by Diagnostic')
plt.ylabel('Count')
plt.xlabel('Diagnostic')
plt.xticks(rotation=45)
plt.show()

# Group the data by 'diagnostic' and 'itch' columns and count the occurrences
grouped_data = metadata.groupby(['diagnostic', 'itch']).size().reset_index(name='count')

# Create a bar plot
plt.figure(figsize=(12, 6))
sns.barplot(data=grouped_data, x='diagnostic', y='count', hue='itch')
plt.title('Count of "Itch" by Diagnostic')
plt.ylabel('Count')
plt.xlabel('Diagnostic')
plt.xticks(rotation=45)
plt.show()

# Create a box plot
plt.figure(figsize=(12, 6))
sns.boxplot(data=metadata, x='diagnostic', y='age')
plt.title('Age Distribution by Diagnostic')
plt.ylabel('Age')
plt.xlabel('Diagnostic')
plt.xticks(rotation=45)
plt.show()

"""# Model Training"""

# Filter the metadata to include only the images present in the dataset
metadata_images = metadata['img_id'].apply(lambda x: os.path.exists(f'{combined_dataset_folder}/{x}'))
metadata = metadata[metadata_images]

# Use LabelEncoder to transform the 'diagnostic' labels into integers
label_encoder = LabelEncoder()
metadata['diagnostic'] = label_encoder.fit_transform(metadata['diagnostic'])

# Get the mapping from labels to integers
label_mapping = {label: index for index, label in enumerate(label_encoder.classes_)}

label_mapping

class_distribution = metadata['diagnostic'].value_counts()
print(class_distribution)

# Giving full form of labels
lesion_type = {
    'ACK': 'Actinic keratoses',
    'BCC': 'Basal cell carcinoma',
    'MEL': 'Melanoma',
    'NEV': 'Melanocytic nevi',
    'SCC': 'Squamous Cell Carcinoma',
    'SEK': 'VSeborrheic Keratosis'
}

metadata['skin_cancer_history'] = metadata['skin_cancer_history'].map({'True': 1, 'False': 0})
metadata['changed'] = metadata['changed'].map({'True': 1, 'False': 0})
metadata['itch'] = metadata['itch'].map({'True': 1, 'False': 0})
metadata['grew'] = metadata['grew'].map({'True': 1, 'False': 0})
metadata['hurt'] = metadata['hurt'].map({'True': 1, 'False': 0})
metadata['bleed'] = metadata['bleed'].map({'True': 1, 'False': 0})
metadata['elevation'] = metadata['elevation'].map({'True': 1, 'False': 0})
metadata['changed'] = metadata['changed'].map({'True': 1, 'False': 0})

# Split the data into a training set and a validation set
train_data, val_data = train_test_split(metadata, test_size=0.2, random_state=42)

from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Define data augmentation
datagen = ImageDataGenerator(
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True)

# Define a function to load and preprocess images
def load_and_preprocess_image(image_path, img_size=(224, 224)):
    # Load the image
    img = load_img(image_path, target_size=img_size)
    # Convert the image to an array
    img = img_to_array(img)
    return img

# Load and preprocess the images in the training set
train_images = np.array([load_and_preprocess_image(f'{combined_dataset_folder}/{img_id}') for img_id in train_data['img_id']])
train_labels = to_categorical(train_data['diagnostic'].values)

# Load and preprocess the images in the validation set
val_images = np.array([load_and_preprocess_image(f'{combined_dataset_folder}/{img_id}') for img_id in val_data['img_id']])
val_labels = to_categorical(val_data['diagnostic'].values)

# Fit the datagen object to your training data
datagen.fit(train_images)

patient_features = ['age', 'skin_cancer_history', 'itch', 'grew', 'hurt', 'changed', 'bleed', 'elevation', 'diameter_1', 'diameter_2']

# Load and preprocess the patient data
# Fill NaN values with 0
train_data[patient_features] = train_data[patient_features].fillna(0).astype(int)
val_data[patient_features] = val_data[patient_features].fillna(0).astype(int)

# Apply the StandardScaler
scaler = StandardScaler()
train_patient_data = scaler.fit_transform(train_data[patient_features].values)
val_patient_data = scaler.transform(val_data[patient_features].values)

!pip install joblib

import joblib

# Save the scaler to a file
joblib.dump(scaler, '/content/drive/My Drive/Skin Cancer/scaler.pkl')

from sklearn.utils import class_weight

labels = train_data['diagnostic'].values

sample_weights = class_weight.compute_sample_weight(class_weight='balanced', y=labels)
class_weights = {i: weight for i, weight in enumerate(np.unique(sample_weights))}

# Load the EfficientNetB0 model
base_model = EfficientNetB0(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# Freeze the base model
base_model.trainable = False

# Define the patient data input
patient_data_input = Input(shape=(10,))

# Define the patient data sub-model
patient_data_model = Dense(32, activation='relu', kernel_regularizer=l2(0.01))(patient_data_input)
patient_data_model = Dense(32, activation='relu', kernel_regularizer=l2(0.01))(patient_data_model)

# Flatten the output of the base model
flattened_output = Flatten()(base_model.output)

# Define the combined model
combined_output = Concatenate()([flattened_output, patient_data_model])
combined_output = Dense(len(label_encoder.classes_), activation='softmax')(combined_output)

# Create the combined model
combined_model = Model(inputs=[base_model.input, patient_data_input], outputs=combined_output)

# Define the early stopping callback
early_stopping = EarlyStopping(monitor='val_loss', patience=3)

# Compile the combined model
combined_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

combined_model.summary()

def multiple_inputs_gen(image_datagen, X1, X2, y, batch_size):
    genX1 = image_datagen.flow(X1, y, batch_size=batch_size, seed=1)
    genX2 = image_datagen.flow(X1, X2, batch_size=batch_size, seed=1)
    while True:
        X1i = genX1.next()
        X2i = genX2.next()
        yield [X1i[0], X2i[1]], X1i[1]  # Yield [image, other features] and label

# Create the generator
train_gen = multiple_inputs_gen(datagen, train_images, train_patient_data, train_labels, batch_size=10)

# Train the model
combined_model.fit(train_gen,
                   steps_per_epoch=len(train_images) // 10,
                   validation_data=([val_images, val_patient_data], val_labels),
                   epochs=20,
                   class_weight=class_weights)

combined_model.save('/content/drive/My Drive/Skin Cancer/mendely_model.h5')

"""# Image Model"""

!find '/content/mendely/' -name "aug" -exec rm -rf {} \;

df = pd.read_csv('metadata.csv')

metadata=df

from tensorflow.keras.preprocessing.image import ImageDataGenerator
import os

# Define the data augmentation parameters
  datagen = ImageDataGenerator(
      rotation_range=40,
      width_shift_range=0.2,
      height_shift_range=0.2,
      shear_range=0.2,
      zoom_range=0.2,
      horizontal_flip=True,
      fill_mode='nearest'
)

# Select the images from the 'NEV' class
nev_images = metadata[metadata['diagnostic'] == 'MEL']['img_id'].values

# Define the directory where the original images are located
image_dir = "/content/mendely/"

# Define the directory where the augmented images should be saved
augmented_dir = "/content/mendely_augmented"

# Create the augmented images directory if it doesn't exist
if not os.path.exists(augmented_dir):
    os.makedirs(augmented_dir)

# Perform augmentation for each image
for image_name in nev_images:
    # Load the image
    img_path = os.path.join(image_dir, image_name)  # Correct the file extension here
    img = load_img(img_path)  # Load the image as a PIL image
    x = img_to_array(img)  # Convert the PIL image to a numpy array
    x = x.reshape((1,) + x.shape)  # Reshape the image to (1, height, width, channels)

    # Perform augmentation and save the augmented images
    i = 0
    for batch in datagen.flow(x, batch_size=1, save_to_dir=augmented_dir, save_prefix='aug', save_format='png'):
        i += 1
        if i >= 5:  # Save 5 augmented images for each original image
            break

import pandas as pd
import os

# Define the directory where the augmented images are saved
augmented_dir = "/content/mendely_augmented"

# Get the list of augmented image filenames
augmented_images = os.listdir(augmented_dir)

# Remove the file extension from the image filenames
augmented_images = [image[:-4] for image in augmented_images]

# Create a dataframe for the augmented images with the same columns as the original dataframe
augmented_df = pd.DataFrame(columns=metadata.columns)

# Set the 'img_id' column to the augmented image filenames
augmented_df['img_id'] = augmented_images

# Set the 'diagnostic' column to 'NEV' for all augmented images
augmented_df['diagnostic'] = 'NEV'

# Append the augmented dataframe to the original dataframe
metadata = pd.concat([metadata, augmented_df], ignore_index=True)

# Shuffle the dataframe
metadata = metadata.sample(frac=1).reset_index(drop=True)

# Save the updated dataframe
metadata.to_csv('updated_metadata.csv', index=False)

import os

combined_dir = '/content/mendely/'
os.makedirs(combined_dir, exist_ok=True)

augmented_images_dir = '/content/mendely_augmented'

# Move the augmented images to the combined directory
for image in os.listdir(augmented_images_dir):
    shutil.move(os.path.join(augmented_images_dir, image), os.path.join(combined_dir, image))

metadata['diagnostic'].value_counts()

df = pd.read_csv('updated_metadata.csv')

df.info()

from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from keras.preprocessing.image import ImageDataGenerator
from keras.layers import Dropout

datagen = ImageDataGenerator(
    rescale=1.0/255.0,
    validation_split=0.2
)

# Specify the path to the directory containing the augmented images
augmented_dir = '/content/mendely/'

# Split the metadata into training and validation dataframes
train_df, val_df = train_test_split(metadata, test_size=0.2, stratify=metadata['diagnostic'], random_state=42)

batch_size = 32

# Apply data augmentation to training data
train_generator = datagen.flow_from_dataframe(
    dataframe=train_df,
    directory='/content/mendely/',
    x_col="img_id",
    y_col="diagnostic",
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical',
    seed=42
)

# Define the validation data generator (without augmentation)
validation_generator = datagen.flow_from_dataframe(
    dataframe=val_df,
    directory='/content/mendely/',
    x_col="img_id",
    y_col="diagnostic",
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical',
    seed=42
)

# Define CNN model with dropout layers
model = Sequential()
model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3)))
model.add(MaxPooling2D(2, 2))
model.add(Dropout(0.25))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(2, 2))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(6, activation='softmax'))

# Compile model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

model.fit(
    train_generator,
    steps_per_epoch=train_generator.n // batch_size,
    validation_data=validation_generator,
    validation_steps=validation_generator.n // batch_size,
    epochs=20
)

model.save('/content/drive/My Drive/Skin Cancer/image_model.h5')

import json

# Save the class_indices dictionary to a JSON file
with open('/content/drive/My Drive/Skin Cancer/class_indices.json', 'w') as f:
    json.dump(train_generator.class_indices, f)

"""# Validation"""

import keras

model = keras.models.load_model('/content/drive/My Drive/Skin Cancer/mendely_model.h5')

# Updated Codeß
import matplotlib.pyplot as plt
import numpy as np

# Use the model to make predictions
predictions = model.predict([val_images, val_patient_data])

# Convert predictions from one-hot encoding to labels
predicted_labels = np.argmax(predictions, axis=-1)

# Convert the numeric labels back to original abbreviated labels
predicted_labels_abbrev = label_encoder.inverse_transform(predicted_labels)

# Convert abbreviated labels to full names
predicted_labels_full = [lesion_type[label] for label in predicted_labels_abbrev]

# Convert one-hot encoded labels to numeric labels
val_labels_numeric = np.argmax(val_labels, axis=-1)

# Convert the numeric labels back to original abbreviated labels
true_labels_abbrev = label_encoder.inverse_transform(val_labels_numeric)

# Convert abbreviated labels to full names
true_labels_full = [lesion_type[label] for label in true_labels_abbrev]

# Identify unique classes
unique_classes = np.unique(val_labels_numeric)

# Create a plot
fig, axes = plt.subplots(len(unique_classes), 4, figsize=(12, 30))

for i, label in enumerate(unique_classes):
    # Find the first two occurrences of the class in the validation set
    indices = np.where(val_labels_numeric == label)[0][:2]

    for j, index in enumerate(indices):
        # Extract the image and normalize it for display
        image = val_images[index]
        image_normalized = image.astype('float32') / 255

        # Display the image with the true and predicted labels
        axes[i, 2*j].imshow(image_normalized)
        axes[i, 2*j+1].imshow(image_normalized)
        axes[i, 2*j].set_title(f"Predicted: {lesion_type[predicted_labels_abbrev[index]]}")
        axes[i, 2*j+1].set_title(f"True: {lesion_type[true_labels_abbrev[index]]}")

plt.tight_layout()
plt.show()

import matplotlib.pyplot as plt
import numpy as np

# Use the model to make predictions
predictions = model.predict([val_images, val_patient_data])

# Convert predictions from one-hot encoding to labels
predicted_labels = np.argmax(predictions, axis=-1)

# Convert the numeric labels back to original abbreviated labels
predicted_labels_abbrev = label_encoder.inverse_transform(predicted_labels)

# Convert abbreviated labels to full names
predicted_labels_full = [lesion_type[label] for label in predicted_labels_abbrev]

# Convert one-hot encoded labels to numeric labels
val_labels_numeric = np.argmax(val_labels, axis=-1)

# Convert the numeric labels back to original abbreviated labels
true_labels_abbrev = label_encoder.inverse_transform(val_labels_numeric)

# Convert abbreviated labels to full names
true_labels_full = [lesion_type[label] for label in true_labels_abbrev]

# Display the first 10 images, their predicted labels, and the true labels
fig, axes = plt.subplots(10, 2, figsize=(10, 20))

for i, ax in enumerate(axes):
    # Normalize the image to [0, 1]
    img_normalized = val_images[i].astype('float32') / 255

    # Display the image
    ax[0].imshow(img_normalized)
    ax[1].imshow(img_normalized)

    # Display the predicted label
    ax[0].set_title(f'Predicted: {predicted_labels_full[i]}')

    # Display the true label
    ax[1].set_title(f'True: {true_labels_full[i]}')

plt.tight_layout()
plt.show()

# Get the true labels and predicted labels (replace these with your actual labels)
y_true = np.argmax(val_labels, axis=1)
y_pred = np.argmax(predictions, axis=1)

# Compute accuracy
accuracy = accuracy_score(y_true, y_pred)
print(f'Accuracy: {accuracy}')

# Compute F1-score
f1 = f1_score(y_true, y_pred, average='weighted')  # Use 'weighted' for multi-class problems
print(f'F1-score: {f1}')

# Compute confusion matrix
conf_mat = confusion_matrix(y_true, y_pred)
print('Confusion Matrix:')
print(conf_mat)

# Plot the confusion matrix
plt.figure(figsize=(10, 7))
sns.heatmap(conf_mat, annot=True, fmt='d', cmap='Blues')
plt.xlabel('Predicted')
plt.ylabel('True')
plt.show()

# Compute ROC curve and AUC for each class
fpr = dict()
tpr = dict()
roc_auc = dict()
num_classes = val_labels.shape[1]
for i in range(num_classes):
    fpr[i], tpr[i], _ = roc_curve(y_true == i, predictions[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])

# Plot the ROC curve
plt.figure(figsize=(10, 7))
for i in range(num_classes):
    plt.plot(fpr[i], tpr[i], label=f'ROC curve of class {i} (area = {roc_auc[i]:.2f})')
plt.plot([0, 1], [0, 1], 'k--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")
plt.show()

"""# Testing"""

from sklearn.preprocessing import LabelEncoder, StandardScaler
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
import numpy as np
from google.colab import files
from io import BytesIO

import json
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array

# Load the previously trained model
model = load_model('/content/drive/My Drive/Skin Cancer/image_model.h5')

# Load the class_indices dictionary from the JSON file
with open('/content/drive/My Drive/Skin Cancer/class_indices.json', 'r') as f:
    class_indices = json.load(f)

# Create a reverse mapping dictionary by swapping the keys and values
reverse_mapping = {v: k for k, v in class_indices.items()}

# Load and preprocess the sample image
image_path = 'PAT_46_881_939.png'
image = load_img(image_path, target_size=(224, 224))  # Resize the image to match the input size of the model
image_array = img_to_array(image)  # Convert the image to a numpy array
image_array = image_array / 255.0  # Normalize the image to [0, 1]
image_array = np.expand_dims(image_array, axis=0)  # Add a batch dimension

patient_data = {
    'age': 32,
    'skin_cancer_history': 'False',
    'itch': 'False',
    'grew': 'False',
    'hurt': 'False',
    'changed': 'True',
    'bleed': 'False',
    'elevation': 'True',
    'diameter_1': 0,
    'diameter_2': 0
}

# Convert 'True' and 'False' to integers
for key, value in patient_data.items():
    if value == 'True':
        patient_data[key] = 1.0
    elif value == 'False':
        patient_data[key] = 0.0

features = np.array([list(patient_data.values())])


# Predict the class of the sample image
predictions = model.predict(image_array)
predicted_class = np.argmax(predictions, axis=1)

# Get the full form of the predicted class
lesion_type_dict = {
    'ACK': 'Actinic keratoses',
    'BCC': 'Basal cell carcinoma',
    'MEL': 'Melanoma',
    'NEV': 'Melanocytic nevi',
    'SCC': 'Squamous Cell Carcinoma',
    'SEK': 'Seborrheic Keratosis'
}

predicted_class_label = reverse_mapping[predicted_class[0]]
predicted_class_fullform = lesion_type_dict[predicted_class_label]

# Classify as cancerous or non-cancerous
cancerous_types = ['Basal cell carcinoma', 'Melanoma', 'Squamous Cell Carcinoma']
if predicted_class_fullform in cancerous_types:
    cancer_status = "Cancerous"
else:
    cancer_status = "Non-cancerous"

print(f'Predicted class: {predicted_class_fullform} ({cancer_status})')

"""# Testing - On Progress"""

# Load model
model = load_model('/content/drive/My Drive/Skin Cancer/mendely_model.h5')

# Load the scaler that was saved during training
scaler = joblib.load('/content/drive/My Drive/Skin Cancer/scaler.pkl')  # Assuming you saved it as 'scaler.pkl'

from PIL import Image
from tensorflow.keras.preprocessing.image import img_to_array
from sklearn.preprocessing import StandardScaler, LabelEncoder
import numpy as np
import joblib

# Load and preprocess image
image_path = 'PAT_161_250_197.png'
image = Image.open(image_path).convert('RGB')
image = image.resize((224, 224))
image = img_to_array(image)
image = np.expand_dims(image, axis=0)
image = image / 255.0  # Normalize pixel values

# Patient features and preprocessing
# Replace with actual patient feature values
patient_data = {
    'age': 32,
    'skin_cancer_history': 'False',
    'itch': 'False',
    'grew': 'False',
    'hurt': 'False',
    'changed': 'True',
    'bleed': 'False',
    'elevation': 'True',
    'diameter_1': 0,
    'diameter_2': 0
}

# Convert 'True' and 'False' to integers
for key, value in patient_data.items():
    if value == 'True':
        patient_data[key] = 1.0
    elif value == 'False':
        patient_data[key] = 0.0

features = np.array([list(patient_data.values())])

features = scaler.transform(features)  # Use the loaded scaler to transform the features


# Make a prediction using your trained model
preds = model.predict([image, features])
predicted_class_index = np.argmax(preds[0])

# Load the LabelEncoder used during training
# For demonstration, we're creating a new one
label_encoder = LabelEncoder()
label_encoder.fit(['NEV', 'BCC', 'ACK', 'SEK', 'SCC', 'MEL'])
predicted_class_label = label_encoder.inverse_transform([predicted_class_index])[0]

# Get the full form of the predicted class
lesion_type_dict = {
    'ACK': 'Actinic keratoses',
    'BCC': 'Basal cell carcinoma',
    'MEL': 'Melanoma',
    'NEV': 'Melanocytic nevi',
    'SCC': 'Squamous Cell Carcinoma',
    'SEK': 'Seborrheic Keratosis'
}
predicted_class_fullform = lesion_type_dict[predicted_class_label]

print(predicted_class_fullform)

