import unittest

import numpy as np
import tensorflow as tf
import tensorflow_probability

import mvg_distributions.covariance_representations as cov_rep
import mvg_distributions.mvg as custom_dist
from mvg_distributions.test.test_losses_base import LossesTestBase

tf_dist = tensorflow_probability.distributions


class TestMultivariateNormal(LossesTestBase):
    def setUp(self):
        super().setUp()
        self.x, self.mvnd_base, self.mvnd_test = self._create_single_mvnd_pair()
        _, self.mvnd_base2, self.mvnd_test2 = self._create_single_mvnd_pair()

    def _create_single_mvnd_pair(self):
        if self.__class__ == TestMultivariateNormal:
            return None, None, None
        else:
            raise NotImplementedError("")

    def test__log_prob(self):
        if self.__class__ == TestMultivariateNormal:
            return

        # i = 0, without sample, i = 1, with sample dim, i = 2, with sample dim == 2
        for i in range(3):
            if i == 1:
                self.x = np.expand_dims(self.x, axis=0)
            if i == 2:
                self.x = np.concatenate((self.x, self.x * 2), axis=0)

            log_prob1 = self.mvnd_test.log_prob(self.x)
            log_prob2 = self.mvnd_base.log_prob(self.x)

            self._asset_allclose_tf_feed(log_prob1, log_prob2)

    def test__prob(self):
        if self.__class__ == TestMultivariateNormal:
            return
        for i in range(3):
            if i == 1:
                self.x = np.expand_dims(self.x, axis=0)
            if i == 2:
                self.x = np.concatenate((self.x, self.x * 2), axis=0)

            prob1 = self.mvnd_test.prob(self.x)
            prob2 = self.mvnd_base.prob(self.x)

            self._asset_allclose_tf_feed(prob1, prob2)

    def test__loc(self):
        if self.__class__ == TestMultivariateNormal:
            return
        loc1 = self.mvnd_test.loc
        loc2 = self.mvnd_base.loc

        self._asset_allclose_tf_feed(loc1, loc2)

    def test__scale(self):
        if self.__class__ == TestMultivariateNormal:
            return
        scale1 = self.mvnd_test.scale
        scale2 = self.mvnd_base.scale.to_dense()

        self._asset_allclose_tf_feed(scale1, scale2)

    def test_stddev(self):
        if self.__class__ == TestMultivariateNormal:
            return
        scale1 = self.mvnd_test.stddev()
        scale2 = self.mvnd_base.stddev()

        self._asset_allclose_tf_feed(scale1, scale2)

    def test_variance(self):
        if self.__class__ == TestMultivariateNormal:
            return
        variance1 = self.mvnd_test.variance()
        variance2 = self.mvnd_base.variance()

        self._asset_allclose_tf_feed(variance1, variance2)

    def test__covariance_matrix(self):
        if self.__class__ == TestMultivariateNormal:
            return
        matrix1 = self.mvnd_test.covariance()
        matrix2 = self.mvnd_base.covariance()

        self._asset_allclose_tf_feed(matrix1, matrix2)

    def test__entropy(self):
        if self.__class__ == TestMultivariateNormal:
            return
        entropy1 = self.mvnd_test.entropy()
        entropy2 = self.mvnd_base.entropy()

        self._asset_allclose_tf_feed(entropy1, entropy2)

    def test__kl_div1(self):
        if self.__class__ == TestMultivariateNormal:
            return

        # Test kl between MultivariateNormal and MultivariateNormal
        kl1 = tf_dist.kl_divergence(self.mvnd_test, self.mvnd_test2)
        kl2 = tf_dist.kl_divergence(self.mvnd_base, self.mvnd_base2)

        self._asset_allclose_tf_feed(kl1, kl2)

    def test__kl_div2(self):
        if self.__class__ == TestMultivariateNormal:
            return

        # Test kl between MultivariateNormal and MultivariateNormalLinearOperator
        kl1 = tf_dist.kl_divergence(self.mvnd_test, self.mvnd_base2)
        kl2 = tf_dist.kl_divergence(self.mvnd_base, self.mvnd_test2)

        self._asset_allclose_tf_feed(kl1, kl2)

        # Check that it's also the same as between tf distributions
        kl3 = tf_dist.kl_divergence(self.mvnd_base, self.mvnd_base2)
        self._asset_allclose_tf_feed(kl1, kl3)

    def test_sample(self):
        if self.__class__ == TestMultivariateNormal:
            return

        eps = self.mvnd_test.cov_obj._get_epsilon(num_samples=1, epsilon=None)
        sample1 = self.mvnd_test.sample_with_epsilon(epsilon=eps)

        sample2 = tf.matmul(self.mvnd_base.scale.to_dense(), tf.transpose(eps, perm=(0, 2, 1)))
        sample2 = tf.squeeze(sample2, axis=2) + self.mvnd_base.loc

        self._asset_allclose_tf_feed(sample1, sample2)

    def test_sample_2(self):
        if self.__class__ == TestMultivariateNormal:
            return

        sample1 = self.mvnd_test.sample(seed=0)
        sample2 = self.mvnd_base.sample(seed=0)

        self._asset_allclose_tf_feed(sample1, sample2)


class TestMultivariateNormalDiag(TestMultivariateNormal):
    def _create_single_mvnd_pair(self):
        x, mu, sigma_sq = self._random_normal_params(cov_rep.CovarianceDiag)

        mvnd_base = tf_dist.MultivariateNormalDiag(loc=mu, scale_diag=np.sqrt(sigma_sq))
        mvnd_test = custom_dist.MultivariateNormalDiag(loc=mu, log_diag_covariance=tf.log(sigma_sq))

        return x, mvnd_base, mvnd_test

    def test__kl_div_unit(self):
        if self.__class__ == TestMultivariateNormal:
            return

        custom_unit_mvnd = custom_dist.IsotropicMultivariateNormal(shape=self.mvnd_test.loc.shape,
                                                                   dtype=self.mvnd_test.loc.dtype)
        kl1 = tf_dist.kl_divergence(self.mvnd_test, custom_unit_mvnd)

        mu = tf.zeros(shape=self.mvnd_base.loc.shape)
        sigma_sq = tf.ones(shape=self.mvnd_base.loc.shape)
        tf_unit_mvnd = tf_dist.MultivariateNormalDiag(loc=mu, scale_diag=tf.sqrt(sigma_sq))
        kl2 = tf_dist.kl_divergence(self.mvnd_base, tf_unit_mvnd)

        self._asset_allclose_tf_feed(kl1, kl2)


class TestMultivariateNormalChol(TestMultivariateNormal):
    def _create_single_mvnd_pair(self):
        x, mu, covariance = self._random_normal_params(cov_rep.CovarianceCholesky)
        chol_covariance = np.linalg.cholesky(covariance)
        log_diag_chol_covariance = np.log(np.diagonal(chol_covariance, axis1=1, axis2=2))

        mvnd_base = tf_dist.MultivariateNormalFullCovariance(loc=mu, covariance_matrix=covariance)
        mvnd_test = custom_dist.MultivariateNormalChol(loc=mu, chol_covariance=chol_covariance,
                                                       log_diag_chol_covariance=log_diag_chol_covariance)

        return x, mvnd_base, mvnd_test


class TestMultivariateNormalCholPrec(TestMultivariateNormal):
    def _create_single_mvnd_pair(self):
        x, mu, covariance = self._random_normal_params(cov_rep.CovarianceCholesky)
        precision = np.linalg.inv(covariance)
        chol_precision = np.linalg.cholesky(precision)
        log_diag_chol_precision = np.log(np.diagonal(chol_precision, axis1=1, axis2=2))

        mvnd_base = tf_dist.MultivariateNormalFullCovariance(loc=mu, covariance_matrix=covariance)
        mvnd_test = custom_dist.MultivariateNormalChol(loc=mu, chol_precision=chol_precision,
                                                       log_diag_chol_precision=log_diag_chol_precision)

        return x, mvnd_base, mvnd_test

    @unittest.skip("Samples with upper triangular matrix, need to fix")
    def test_sample(self):
        pass

    @unittest.skip("Samples with upper triangular matrix, need to fix")
    def test_sample_2(self):
        pass


class TestMultivariateNormalCholFilters(TestMultivariateNormal):
    def _create_single_mvnd_pair(self):
        x, mu, covariance, weights, filters, log_diag = self._random_normal_params(cov_rep.PrecisionConvCholFilters)

        mvnd_base = tf_dist.MultivariateNormalFullCovariance(loc=mu, covariance_matrix=covariance)

        img_size = int(np.sqrt(self.features_size))
        img_shape = (self.batch_size, img_size, img_size, 1)
        mvnd_test = custom_dist.MultivariateNormalPrecCholFilters(loc=mu, weights_precision=weights,
                                                                  filters_precision=filters,
                                                                  log_diag_chol_precision=log_diag,
                                                                  sample_shape=img_shape)

        return x, mvnd_base, mvnd_test

    @staticmethod
    def _upper_triangular_chol_matrix(matrix):
        upper_chol_matrix = tf.cholesky(tf.matrix_inverse(matrix))
        upper_chol_matrix = tf.matrix_inverse(upper_chol_matrix)
        return tf.matrix_transpose(upper_chol_matrix)

    def test_sample(self):
        eps = self.mvnd_test.cov_obj._get_epsilon(num_samples=1, epsilon=None)
        sample1 = self.mvnd_test.sample_with_epsilon(epsilon=eps)

        # Chol filters samples with the transpose of the inverse of Cholesky of the precision matrix
        # i.e. with a valid upper triangular decomposition of the covariance
        upper_chol_covariance = self._upper_triangular_chol_matrix(self.mvnd_base.covariance())

        sample2 = tf.matmul(upper_chol_covariance, eps, transpose_b=True)
        sample2 = tf.squeeze(sample2, axis=2) + self.mvnd_base.loc

        self._asset_allclose_tf_feed(sample1, sample2)

        # Check that sqrt_covariance is indeed a valid decomposition by reconstructing the covariance matrix
        recons_covariance = tf.matmul(upper_chol_covariance, upper_chol_covariance, transpose_b=True)
        self._asset_allclose_tf_feed(recons_covariance, self.mvnd_base.covariance())

    @unittest.skip("Samples with upper triangular matrix, need to fix")
    def test_sample_2(self):
        pass

    def test_sample_sparse_solver(self):
        sample1 = self.mvnd_test.sample(seed=0)
        sample2 = self.mvnd_test.sample_with_sparse_solver(seed=0, sess=self.sess,
                                                           feed_dict=self.tf_feed)

        self._asset_allclose_tf_feed(sample1, sample2)

    def test_chol_covariance_sparse_solver(self):
        covariance1 = self.mvnd_base.covariance()
        chol_covariance1 = self._upper_triangular_chol_matrix(covariance1)

        chol_covariance2 = self.mvnd_test.upper_chol_covariance_with_sparse_solver(sess=self.sess,
                                                                                   feed_dict=self.tf_feed)

        covariance2 = np.matmul(chol_covariance2, chol_covariance2.transpose((0, 2, 1)))

        self._asset_allclose_tf_feed(chol_covariance1, chol_covariance2)
        self._asset_allclose_tf_feed(covariance1, covariance2)

    def test_covariance_sparse_solver(self):
        covariance1 = self.mvnd_base.covariance()
        covariance2 = self.mvnd_test.covariance_with_sparse_solver(sess=self.sess,
                                                                   feed_dict=self.tf_feed)

        self._asset_allclose_tf_feed(covariance1, covariance2)

    def test_variance_sparse_solver(self):
        variance1 = self.mvnd_base.variance()
        variance2 = self.mvnd_test.variance_with_sparse_solver(sess=self.sess,
                                                               feed_dict=self.tf_feed,
                                                               use_iterative_solver=True)

        self._asset_allclose_tf_feed(variance1, variance2)

    def test_variance_sparse_solver2(self):
        variance1 = self.mvnd_base.variance()
        variance2 = self.mvnd_test.variance_with_sparse_solver(sess=self.sess,
                                                               feed_dict=self.tf_feed,
                                                               use_iterative_solver=False)
        self._asset_allclose_tf_feed(variance1, variance2)

    def test_conditional_mean(self):
        # Condition on 1, 2 or 5 pixels
        num_x_cond_list = [1, 2, 5]
        solver_methods = custom_dist.MultivariateNormalPrecCholFilters.CondMeanSolver

        for num_x_cond in num_x_cond_list:
            # Get random conditioning values, and random indices
            np_x_cond = np.random.normal(size=(self.batch_size, num_x_cond)).astype(self.dtype.as_numpy_dtype)
            np_x_cond_idx = np.random.choice(self.features_size, num_x_cond, replace=False)

            cond_means = [None] * len(solver_methods)
            for i, solver_method in enumerate(solver_methods):
                cond_means[i] = self.mvnd_test.conditional_mean(sess=self.sess,
                                                                feed_dict=self.tf_feed,
                                                                x_known=np_x_cond,
                                                                x_known_idx=np_x_cond_idx,
                                                                solver_method=solver_method)

            # Check that we get the same result regardless of the solver method
            for i in range(1, len(cond_means)):
                self._assert_allclose_np_np(cond_means[0], cond_means[i])


class TestMultivariateNormalCholFiltersDilation(TestMultivariateNormalCholFilters):
    def _create_single_mvnd_pair(self):
        outputs = self._random_normal_params(cov_rep.PrecisionDilatedConvCholFilters)
        x, mu, covariance, weights, filters, dilation_rates, log_diag = outputs

        mvnd_base = tf_dist.MultivariateNormalFullCovariance(loc=mu, covariance_matrix=covariance)

        img_size = int(np.sqrt(self.features_size))
        img_shape = (self.batch_size, img_size, img_size, 1)
        mvnd_test = custom_dist.MultivariateNormalPrecCholFiltersDilation(loc=mu, weights_precision=weights,
                                                                          filters_precision=filters,
                                                                          log_diag_chol_precision=log_diag,
                                                                          sample_shape=img_shape,
                                                                          dilation_rates=dilation_rates)

        return x, mvnd_base, mvnd_test

    @unittest.skip("Sparse sampler not implemented for dilated filters")
    def test_sample_sparse_solver(self):
        pass

    @unittest.skip("Sparse sampler not implemented for dilated filters")
    def test_chol_covariance_sparse_solver(self):
        pass

    @unittest.skip("Sparse solver not implemented for dilated filters")
    def test_covariance_sparse_solver(self):
        pass

    @unittest.skip("Sparse solver not implemented for dilated filters")
    def test_variance_sparse_solver(self):
        pass

    @unittest.skip("Sparse solver not implemented for dilated filters")
    def test_variance_sparse_solver2(self):
        pass

    @unittest.skip("Sparse solver not implemented for dilated filters")
    def test_conditional_mean(self):
        pass


class TestIsotropicMultivariateNormal(TestMultivariateNormal):
    def _create_single_mvnd_pair(self):
        # Create isotropic Gaussian N(0,I)
        x, mu, sigma_sq = self._random_normal_params(cov_rep.CovarianceDiag)
        mu[:] = 0
        sigma_sq[:] = 1

        mvnd_base = tf_dist.MultivariateNormalDiag(loc=mu, scale_diag=np.sqrt(sigma_sq))
        mvnd_test = custom_dist.IsotropicMultivariateNormal(shape=tf.shape(mu), dtype=tf.float32)

        return x, mvnd_base, mvnd_test


if __name__ == '__main__':
    unittest.main()
