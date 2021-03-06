import tensorflow as tf

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # /*
sys.path.append(os.path.dirname(__file__))  # /models/

from abstract_model import AbstractModel
from tf_utils import layers, layers_exp, regularization


class RBFResNet(AbstractModel):

    def __init__(self,
                 input_shape,
                 class_count,
                 batch_size=128,
                 learning_rate_policy=1e-2,
                 block_properties=layers.ResidualBlockProperties([3, 3]),
                 group_lengths=[3, 3, 3],
                 base_width=16,
                 widening_factor=1,
                 weight_decay=5e-4,
                 training_log_period=1,
                 name='ResNet'):
        self.completed_epoch_count = 0
        self.block_properties = block_properties
        self.group_lengths = group_lengths
        self.depth = 1 + sum(group_lengths) * len(block_properties.ksizes) + 1
        self.zagoruyko_depth = self.depth - 1 + len(group_lengths)
        self.base_width = base_width
        self.widening_factor = widening_factor
        self.weight_decay = weight_decay
        super().__init__(
            input_shape=input_shape,
            class_count=class_count,
            batch_size=batch_size,
            learning_rate_policy=learning_rate_policy,
            training_log_period=training_log_period,
            name=name)

    def _build_graph(self, learning_rate, epoch, is_training):
        from layers import conv

        # Input image and labels placeholders
        input_shape = [None] + list(self.input_shape)
        output_shape = [None, self.class_count]
        input = tf.placeholder(tf.float32, shape=input_shape)
        target = tf.placeholder(tf.float32, shape=output_shape)

        # Hidden layers
        h = layers_exp.rbf_resnet(
            input,
            is_training=is_training,
            base_width=self.base_width,
            widening_factor=self.widening_factor,
            group_lengths=self.group_lengths)

        # Global pooling and softmax classification
        h = tf.reduce_mean(h, axis=[1, 2], keep_dims=True)
        logits = conv(h, 1, self.class_count)
        logits = tf.reshape(logits, [-1, self.class_count])
        probs = tf.nn.softmax(logits)

        # Loss
        clipped_probs = tf.clip_by_value(probs, 1e-10, 1.0)
        loss = -tf.reduce_mean(target * tf.log(clipped_probs))

        # Regularization
        w_vars = filter(lambda x: 'weights' in x.name, tf.global_variables())
        loss += self.weight_decay*regularization.l2_regularization(w_vars)

        # Optimization
        optimizer = tf.train.MomentumOptimizer(learning_rate, 0.9)
        training_step = optimizer.minimize(loss)

        # Dense predictions and labels
        preds, dense_labels = tf.argmax(probs, 1), tf.argmax(target, 1)

        # Other evaluation measures
        accuracy = tf.reduce_mean(
            tf.cast(tf.equal(preds, dense_labels), tf.float32))

        #writer = tf.summary.FileWriter('logs', self._sess.graph)

        return AbstractModel.EssentialNodes(
            input=input,
            target=target,
            probs=probs,
            loss=loss,
            training_step=training_step,
            evaluation={'accuracy': accuracy})
