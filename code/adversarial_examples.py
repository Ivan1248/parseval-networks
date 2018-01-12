import tensorflow as tf
from tensorflow.python.platform import app
from tensorflow.python.platform import flags

from cleverhans.attacks import fgsm
from cleverhans.utils_keras import cnn_model
from cleverhans.utils_tf import model_train, model_eval, batch_eval

FLAGS = flags.FLAGS

flags.DEFINE_string('train_dir', '/tmp', 'Directory storing the saved model.')
flags.DEFINE_string(
    'filename', 'cifar10.ckpt', 'Filename to save model under.')
flags.DEFINE_integer('nb_epochs', 10, 'Number of epochs to train model')
flags.DEFINE_integer('batch_size', 128, 'Size of training batches')
flags.DEFINE_float('learning_rate', 0.001, 'Learning rate for training')


def main(argv=None):
    tf.set_random_seed(1234)

    model = cnn_model(img_rows=32, img_cols=32, channels=3)
    predictions = model(x)
    print("Defined TensorFlow model graph.")

    def evaluate():
        # Evaluate the accuracy of the CIFAR10 model on legitimate test
        # examples
        eval_params = {'batch_size': FLAGS.batch_size}
        accuracy = model_eval(sess, x, y, predictions, X_test, Y_test,
                              args=eval_params)
        assert X_test.shape[0] == 10000, X_test.shape
        print('Test accuracy on legitimate test examples: ' + str(accuracy))

    # Train an CIFAR10 model
    train_params = {
        'nb_epochs': FLAGS.nb_epochs,
        'batch_size': FLAGS.batch_size,
        'learning_rate': FLAGS.learning_rate
    }
    model_train(sess, x, y, predictions, X_train, Y_train,
                evaluate=evaluate, args=train_params)

    # Craft adversarial examples using Fast Gradient Sign Method (FGSM)
    adv_x = fgsm(x, predictions, eps=0.3)
    eval_params = {'batch_size': FLAGS.batch_size}
    X_test_adv, = batch_eval(sess, [x], [adv_x], [X_test], args=eval_params)
    assert X_test_adv.shape[0] == 10000, X_test_adv.shape

    # Evaluate the accuracy of the CIFAR10 model on adversarial examples
    accuracy = model_eval(sess, x, y, predictions, X_test_adv, Y_test,
                          args=eval_params)
    print('Test accuracy on adversarial examples: ' + str(accuracy))

    print("Repeating the process, using adversarial training")
    # Redefine TF model graph
    model_2 = cnn_model(img_rows=32, img_cols=32, channels=3)
    predictions_2 = model_2(x)
    adv_x_2 = fgsm(x, predictions_2, eps=0.3)
    predictions_2_adv = model_2(adv_x_2)

    def evaluate_2():
        # Evaluate the accuracy of the adversarialy trained CIFAR10 model on
        # legitimate test examples
        eval_params = {'batch_size': FLAGS.batch_size}
        accuracy = model_eval(sess, x, y, predictions_2, X_test, Y_test,
                              args=eval_params)
        print('Test accuracy on legitimate test examples: ' + str(accuracy))

        # Evaluate the accuracy of the adversarially trained CIFAR10 model on
        # adversarial examples
        accuracy_adv = model_eval(sess, x, y, predictions_2_adv, X_test,
                                  Y_test, args=eval_params)
        print('Test accuracy on adversarial examples: ' + str(accuracy_adv))

    # Perform adversarial training
    model_train(sess, x, y, predictions_2, X_train, Y_train,
                predictions_adv=predictions_2_adv, evaluate=evaluate_2,
                args=train_params)

    # Evaluate the accuracy of the CIFAR10 model on adversarial examples
    accuracy = model_eval(sess, x, y, predictions_2_adv, X_test, Y_test,
                          args=eval_params)
    print('Test accuracy on adversarial examples: ' + str(accuracy))


if __name__ == '__main__':
    app.run()