# Copyright 2018 The TensorFlow Probability Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Tests for ExponentiatedQuadratic."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import parameterized

import numpy as np
import tensorflow.compat.v2 as tf

import tensorflow_probability as tfp
from tensorflow.python.framework import test_util  # pylint: disable=g-direct-tensorflow-import


@test_util.run_all_in_graph_and_eager_modes
class ExponentiatedQuadraticTest(tf.test.TestCase, parameterized.TestCase):

  def testMismatchedFloatTypesAreBad(self):
    tfp.math.psd_kernels.ExponentiatedQuadratic(
        1, 1)  # Should be OK (float32 fallback).
    tfp.math.psd_kernels.ExponentiatedQuadratic(np.float32(1.),
                                                1.)  # Should be OK.
    with self.assertRaises(TypeError):
      tfp.math.psd_kernels.ExponentiatedQuadratic(
          np.float32(1.), np.float64(1.))

  @parameterized.parameters(
      {'feature_ndims': 1, 'dims': 3},
      {'feature_ndims': 1, 'dims': 4},
      {'feature_ndims': 2, 'dims': 2},
      {'feature_ndims': 2, 'dims': 3},
      {'feature_ndims': 3, 'dims': 2},
      {'feature_ndims': 3, 'dims': 3})
  def testValuesAreCorrect(self, feature_ndims, dims):
    amplitude = 5.
    length_scale = .2

    np.random.seed(42)
    k = tfp.math.psd_kernels.ExponentiatedQuadratic(amplitude, length_scale,
                                                    feature_ndims)
    shape = [dims] * feature_ndims
    for _ in range(5):
      x = np.random.uniform(-1, 1, size=shape).astype(np.float32)
      y = np.random.uniform(-1, 1, size=shape).astype(np.float32)
      self.assertAllClose(
          amplitude ** 2 * np.exp(
              -np.float32(.5) * np.sum((x - y)**2) / length_scale**2),
          self.evaluate(k.apply(x, y)))

  def testNoneShapes(self):
    k = tfp.math.psd_kernels.ExponentiatedQuadratic(
        amplitude=np.reshape(np.arange(12.), [2, 3, 2]))
    self.assertEqual([2, 3, 2], k.batch_shape.as_list())

  def testShapesAreCorrect(self):
    k = tfp.math.psd_kernels.ExponentiatedQuadratic(
        amplitude=1., length_scale=1.)

    x = np.ones([4, 3], np.float32)
    y = np.ones([5, 3], np.float32)

    self.assertAllEqual([4, 5], k.matrix(x, y).shape)
    self.assertAllEqual(
        [2, 4, 5],
        k.matrix(tf.stack([x]*2), tf.stack([y]*2)).shape)

    k = tfp.math.psd_kernels.ExponentiatedQuadratic(
        amplitude=np.ones([2, 1, 1], np.float32),
        length_scale=np.ones([1, 3, 1], np.float32))
    self.assertAllEqual(
        [2, 3, 2, 4, 5],
        #`--'  |  `--'
        #  |   |    `- matrix shape
        #  |   `- from input batch shapes
        #  `- from broadcasting kernel params
        k.matrix(
            tf.stack([x]*2),  # shape [2, 4, 3]
            tf.stack([y]*2)   # shape [2, 5, 3]
        ).shape)

  def testValidateArgs(self):
    # Wrap -1 const in identity so that asserts don't fire at ExpSinSquared
    # construction time.
    minus_1 = tf.identity(tf.convert_to_tensor(-1.))
    with self.assertRaises(tf.errors.InvalidArgumentError):
      k = tfp.math.psd_kernels.ExponentiatedQuadratic(
          minus_1, minus_1, validate_args=True)
      self.evaluate(k.apply([1.], [1.]))

    if not tf.executing_eagerly():
      with self.assertRaises(tf.errors.InvalidArgumentError):
        self.evaluate(k.apply([1.], [1.]))

    # But `None`'s are ok
    k = tfp.math.psd_kernels.ExponentiatedQuadratic(
        None, None, validate_args=True)
    self.evaluate(k.apply([1.], [1.]))


if __name__ == '__main__':
  tf.test.main()
