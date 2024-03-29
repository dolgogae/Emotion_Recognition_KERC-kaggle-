"""
Train our RNN on extracted features or images.
"""
from keras.callbacks import TensorBoard, ModelCheckpoint, EarlyStopping, CSVLogger
from models import ResearchModels
from data import DataSet
import time
import os.path

def train(data_type, seq_length, model, saved_model=None,
          class_limit=None, image_shape=None,
          load_to_memory=False, batch_size=32, nb_epoch=100):
    # Helper: Save the model.

    checkpointer = ModelCheckpoint(filepath='data/checkpoints/weights.hdf5', monitor='val_loss', verbose=1, save_best_only=True)
    # Helper: TensorBoard
    tb = TensorBoard(log_dir=os.path.join('data', 'logs', model))

    # Helper: Stop when we stop learning.
    early_stopper = EarlyStopping(patience=100)

    # Helper: Save results.
    timestamp = time.time()
    csv_logger = CSVLogger(os.path.join('data', 'logs', model + '-' + 'training-' + \
        str(timestamp) + '.log'))

    # Get the data and process it.
    if image_shape is None:
        data = DataSet(
            seq_length=seq_length,
            class_limit=class_limit
        )
    else:
        data = DataSet(
            seq_length=seq_length,
            class_limit=class_limit,
            image_shape=image_shape
        )

    # Get samples per epoch.
    # Multiply by 0.7 to attempt to guess how much of data.data is the train set.
    steps_per_epoch = (len(data.data) * 0.7) // batch_size

    if load_to_memory == True:
        # Get data.
        X, y = data.get_all_sequences_in_memory('train', data_type)
        X_val, y_val = data.get_all_sequences_in_memory('val', data_type)
   
    else:
        # Get generators.
        generator = data.frame_generator(batch_size, 'train', data_type)
        val_generator = data.frame_generator(batch_size, 'val', data_type)
    print(X.shape)
    # Get the model.
    rm = ResearchModels(len(data.classes), model, seq_length, saved_model)

    # Fit!
    if load_to_memory == True:
        # Use standard fit.
        rm.model.fit(
            X,
            y,
            batch_size=batch_size,
            validation_data=(X_val, y_val),
            verbose=1,
            #callbacks=[tb, early_stopper, csv_logger]
            callbacks=[tb, early_stopper, checkpointer],
            epochs=nb_epoch)
    else:
        # Use fit generator.
        rm.model.fit_generator(
            generator=generator,
            steps_per_epoch=steps_per_epoch,
            epochs=nb_epoch,
            verbose=1,
            # callbacks=[tb, early_stopper, csv_logger, checkpointer],
            callbacks=[early_stopper, checkpointer],
            validation_data=val_generator,
            validation_steps=1,
            workers=4)

def main():
    """These are the main training settings. Set each before running
    this file."""
    if os.path.exists(os.path.join('data','checkpoints')) == False: 
        os.makedirs(os.path.join('data','checkpoints'))
        
        
    # model can be one of lrcn, mlp, vgg_16
    model = 'lrcn'
    saved_model = None  # None or weights file
    class_limit = None  # int, can be 1-101 or None
    seq_length = 20
    load_to_memory = True  # pre-load the sequences into memory
    batch_size = 8
    nb_epoch = 1000

    # Chose images or features and image shape based on network.
    if model in ['lrcn']:
        data_type = 'images'
        image_shape = (80, 80, 3)
    elif model in ['vgg_16']:
        data_type = 'images'
        image_shape = (80, 80, 3)
    elif model in ['mlp']:
        data_type = 'features'
        image_shape = None
    elif model in ['conv3D']:
        data_type = 'images'
        image_shape = (80, 80, 3)
    else:
        raise ValueError("Invalid model. See train.py for options.")

    train(data_type, seq_length, model, saved_model=saved_model,
          class_limit=class_limit, image_shape=image_shape,
          load_to_memory=load_to_memory, batch_size=batch_size, nb_epoch=nb_epoch)

if __name__ == '__main__':
    main()
