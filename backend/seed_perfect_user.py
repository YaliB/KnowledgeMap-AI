#!/usr/bin/env python3
"""Inject a complete test user (user_seed01) into the existing Neo4j database."""

import os
import uuid
from datetime import datetime, timezone

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USERNAME") or os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

USER_ID = "user_a63e7852"
NOW = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

concepts_by_name: dict[str, dict] = {}


def concept(name, level, subject, definition, importance, tags):
    node = {
        "id": str(uuid.uuid4()),
        "user_id": USER_ID,
        "name": name,
        "level": level,
        "subject": subject,
        "parent": None,
        "definition": definition,
        "importance": importance,
        "tags": tags,
        "embedding": [],
        "created_at": NOW,
    }
    concepts_by_name[name] = node
    return node


def document(filename, subject, page_count):
    doc_id = str(uuid.uuid4())
    return {
        "id": doc_id,
        "user_id": USER_ID,
        "filename": filename,
        "file_path": f"/uploads/{doc_id}_{filename}",
        "subject": subject,
        "page_count": page_count,
        "status": "done",
        "created_at": NOW,
    }


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------

SUBJECTS = [
    concept(
        "Linear Algebra", "subject", "Linear Algebra",
        "Linear algebra is a branch of mathematics concerned with vector spaces, linear mappings, and systems of linear equations. "
        "It provides the mathematical framework for understanding transformations, matrix operations, and geometric structures. "
        "It is foundational to virtually all areas of science and engineering.",
        10, ["vectors", "matrices", "linear maps", "eigenvalues", "algebra"],
    ),
    concept(
        "Machine Learning", "subject", "Machine Learning",
        "Machine learning is a field of artificial intelligence that develops algorithms enabling systems to learn from data without being explicitly programmed. "
        "It encompasses supervised, unsupervised, and reinforcement learning paradigms. "
        "Applications span computer vision, natural language processing, and predictive analytics.",
        10, ["AI", "algorithms", "data", "models", "learning"],
    ),
    concept(
        "Probability & Statistics", "subject", "Probability & Statistics",
        "Probability and statistics is the mathematical study of uncertainty, randomness, and data analysis. "
        "Probability theory provides the formal framework for modeling random phenomena, while statistics develops methods for collecting, analyzing, and drawing conclusions from data. "
        "Together they form the foundation of data science and scientific reasoning.",
        10, ["probability", "statistics", "randomness", "inference", "data"],
    ),
    concept(
        "Calculus", "subject", "Calculus",
        "Calculus is the mathematical study of continuous change, encompassing differential and integral calculus. "
        "Differential calculus deals with instantaneous rates of change, while integral calculus addresses accumulation and areas under curves. "
        "It is indispensable across all quantitative sciences and engineering disciplines.",
        10, ["derivatives", "integrals", "limits", "continuity", "analysis"],
    ),
]

# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------

LA_TOPICS = [
    concept(
        "Vector Spaces", "topic", "Linear Algebra",
        "A vector space is a collection of objects called vectors that can be added together and scaled by scalars, satisfying a set of axioms. "
        "Vector spaces provide the abstract setting for linear algebra and generalize the familiar notion of geometric vectors. "
        "They appear throughout mathematics, physics, and engineering.",
        9, ["vectors", "scalars", "axioms", "linear algebra", "abstract"],
    ),
    concept(
        "Matrix Operations", "topic", "Linear Algebra",
        "Matrix operations are the fundamental computational tools for working with rectangular arrays of numbers in linear algebra. "
        "Key operations include addition, multiplication, transposition, and inversion, each with specific rules. "
        "These operations form the computational backbone of numerical linear algebra and machine learning.",
        9, ["matrices", "multiplication", "inverse", "determinant", "computation"],
    ),
    concept(
        "Eigenvalues & Eigenvectors", "topic", "Linear Algebra",
        "Eigenvalues and eigenvectors are special scalars and vectors associated with a linear transformation that remain invariant in direction. "
        "For matrix A, an eigenvector v satisfies Av = λv where λ is the eigenvalue. "
        "They reveal intrinsic geometric properties of linear maps and are central to diagonalization and PCA.",
        9, ["eigendecomposition", "eigenvectors", "eigenvalues", "diagonalization", "linear maps"],
    ),
    concept(
        "Linear Transformations", "topic", "Linear Algebra",
        "A linear transformation is a function between vector spaces that preserves vector addition and scalar multiplication. "
        "Every linear transformation can be represented by a matrix relative to a chosen basis. "
        "Linear transformations underpin all of signal processing, computer graphics, and machine learning.",
        8, ["morphisms", "matrices", "vector spaces", "basis", "representation"],
    ),
]

ML_TOPICS = [
    concept(
        "Supervised Learning", "topic", "Machine Learning",
        "Supervised learning trains models on labeled input-output pairs to learn a mapping function that generalizes to unseen data. "
        "The goal is accurate prediction on new examples from a learned approximation of the underlying relationship. "
        "Common algorithms include linear regression, decision trees, and neural networks.",
        9, ["supervised", "labels", "classification", "regression", "generalization"],
    ),
    concept(
        "Unsupervised Learning", "topic", "Machine Learning",
        "Unsupervised learning discovers hidden patterns or structure in data without labeled examples. "
        "The algorithm must infer structure through clustering, density estimation, or dimensionality reduction. "
        "Applications include customer segmentation, anomaly detection, and feature learning.",
        8, ["unsupervised", "clustering", "patterns", "density estimation", "structure"],
    ),
    concept(
        "Neural Networks", "topic", "Machine Learning",
        "Neural networks are computational models inspired by biological brains, consisting of interconnected layers of nodes that process information hierarchically. "
        "They learn representations by adjusting weights through backpropagation during training. "
        "Deep neural networks have achieved state-of-the-art performance across vision, language, and many other domains.",
        9, ["neural networks", "deep learning", "backpropagation", "weights", "layers"],
    ),
    concept(
        "Model Evaluation", "topic", "Machine Learning",
        "Model evaluation encompasses techniques for assessing how well a machine learning model generalizes to unseen data. "
        "Proper evaluation requires careful design of train/validation/test splits and metrics matched to the task. "
        "Without rigorous evaluation, models may overfit or be mismatched to deployment conditions.",
        8, ["evaluation", "generalization", "metrics", "overfitting", "validation"],
    ),
]

PS_TOPICS = [
    concept(
        "Probability Theory", "topic", "Probability & Statistics",
        "Probability theory is the mathematical framework for quantifying uncertainty and studying random phenomena using formal axioms. "
        "Built on Kolmogorov's axioms, it provides tools such as random variables, distributions, and expectation. "
        "It serves as the foundation for statistics, information theory, and machine learning.",
        9, ["probability", "axioms", "random variables", "uncertainty", "Kolmogorov"],
    ),
    concept(
        "Random Variables", "topic", "Probability & Statistics",
        "A random variable assigns numerical values to outcomes of a random experiment, formalizing a quantity that varies with chance. "
        "Random variables may be discrete or continuous, each characterized by a probability distribution. "
        "Expectation, variance, and moments are key summaries of their behavior.",
        8, ["random variables", "distributions", "expectation", "discrete", "continuous"],
    ),
    concept(
        "Statistical Inference", "topic", "Probability & Statistics",
        "Statistical inference draws conclusions about population parameters or hypotheses from sample data using probabilistic reasoning. "
        "It encompasses point estimation, interval estimation, and hypothesis testing. "
        "Inference quantifies uncertainty through confidence intervals and p-values.",
        9, ["inference", "estimation", "hypothesis testing", "confidence", "population"],
    ),
    concept(
        "Bayesian Statistics", "topic", "Probability & Statistics",
        "Bayesian statistics treats probability as a degree of belief updated through evidence using Bayes' theorem. "
        "It combines prior beliefs with the likelihood of observed data to produce posterior distributions. "
        "Bayesian methods naturally handle uncertainty propagation and small-sample inference.",
        9, ["Bayesian", "prior", "posterior", "belief", "Bayes theorem"],
    ),
]

CALC_TOPICS = [
    concept(
        "Differential Calculus", "topic", "Calculus",
        "Differential calculus studies how functions change, formalized through the derivative as an instantaneous rate of change. "
        "Key results include differentiation rules, the chain rule, and mean value theorems characterizing function behavior. "
        "It is essential for optimization, physics, and analysis of dynamical systems.",
        9, ["derivatives", "rates of change", "differentiation", "calculus", "functions"],
    ),
    concept(
        "Integral Calculus", "topic", "Calculus",
        "Integral calculus studies accumulation and area, formalized through the definite integral as the limit of Riemann sums. "
        "The Fundamental Theorem of Calculus links differentiation and integration as inverse operations. "
        "Integration is fundamental to computing areas, volumes, probabilities, and solving differential equations.",
        9, ["integrals", "accumulation", "area", "Riemann sums", "antiderivatives"],
    ),
    concept(
        "Multivariable Calculus", "topic", "Calculus",
        "Multivariable calculus extends single-variable calculus to functions of several variables, introducing gradients, partial derivatives, and multiple integrals. "
        "It describes how functions change in multi-dimensional spaces and enables optimization over vector-valued domains. "
        "Applications include physics, machine learning, and geometric surface analysis.",
        9, ["multivariable", "gradient", "partial derivatives", "vector calculus", "optimization"],
    ),
    concept(
        "Optimization", "topic", "Calculus",
        "Optimization studies finding inputs that maximize or minimize an objective function, subject to constraints. "
        "Mathematical optimization encompasses unconstrained and constrained problems, analyzed through convexity and KKT conditions. "
        "It is the mathematical engine behind machine learning training, operations research, and engineering design.",
        9, ["optimization", "minimum", "maximum", "convexity", "constraints"],
    ),
]

# ---------------------------------------------------------------------------
# Subtopics — Linear Algebra
# ---------------------------------------------------------------------------

LA_SUBTOPICS = [
    # Vector Spaces
    concept(
        "Basis & Dimension", "subtopic", "Linear Algebra",
        "A basis for a vector space is a linearly independent spanning set, making it a minimal spanning set. "
        "The dimension of a vector space is the number of vectors in any basis, an intrinsic property of the space. "
        "Every vector is represented uniquely as a linear combination of basis vectors.",
        7, ["basis", "dimension", "spanning", "linear independence", "coordinates"],
    ),
    concept(
        "Span and Linear Independence", "subtopic", "Linear Algebra",
        "The span of a set of vectors is the set of all linear combinations that can be formed from them, representing the subspace they generate. "
        "A set is linearly independent if no vector can be written as a linear combination of the others. "
        "These concepts define the structural building blocks of vector spaces.",
        7, ["span", "linear independence", "combinations", "subspace", "basis"],
    ),
    concept(
        "Subspaces", "subtopic", "Linear Algebra",
        "A subspace is a subset of a vector space that is itself a vector space under the same operations, closed under addition and scalar multiplication. "
        "Common examples include the null space and column space of a matrix. "
        "Subspaces are key to understanding solution sets of linear systems.",
        7, ["subspace", "null space", "column space", "closure", "vector space"],
    ),
    # Matrix Operations
    concept(
        "Matrix Multiplication", "subtopic", "Linear Algebra",
        "Matrix multiplication combines two matrices by computing dot products of rows and columns, producing a new matrix encoding a composed transformation. "
        "It is non-commutative in general and corresponds to composition of linear maps. "
        "Efficient matrix multiplication underlies modern deep learning and scientific computation.",
        7, ["matrix", "multiplication", "composition", "dot product", "linear maps"],
    ),
    concept(
        "Determinants", "subtopic", "Linear Algebra",
        "The determinant is a scalar associated with a square matrix encoding whether the transformation is invertible and by what factor it scales volumes. "
        "Geometrically, the absolute value of the determinant is the volume scaling factor of the transformation. "
        "A matrix is invertible if and only if its determinant is non-zero.",
        7, ["determinant", "invertibility", "volume", "scalar", "square matrix"],
    ),
    concept(
        "Inverse Matrices", "subtopic", "Linear Algebra",
        "The inverse of a square matrix A is the unique matrix A⁻¹ such that AA⁻¹ = I, the identity matrix. "
        "A matrix is invertible if and only if its determinant is non-zero. "
        "In practice, direct factorization methods like LU decomposition are preferred over explicit inversion.",
        7, ["inverse", "identity", "invertibility", "LU decomposition", "linear systems"],
    ),
    # Eigenvalues & Eigenvectors
    concept(
        "Characteristic Polynomial", "subtopic", "Linear Algebra",
        "The characteristic polynomial of a matrix A is det(A − λI), whose roots are the eigenvalues of A. "
        "Finding eigenvalues reduces to solving this polynomial equation, done numerically for large matrices. "
        "It encodes fundamental invariants of the matrix including trace and determinant.",
        6, ["characteristic polynomial", "eigenvalues", "determinant", "roots", "invariants"],
    ),
    concept(
        "Diagonalization", "subtopic", "Linear Algebra",
        "Diagonalization finds a basis of eigenvectors in which a matrix is diagonal, simplifying computation of matrix powers and functions. "
        "A matrix is diagonalizable if it has enough linearly independent eigenvectors to form a complete basis. "
        "Diagonalization underlies PCA and systems of linear differential equations.",
        7, ["diagonalization", "eigenvectors", "basis", "matrix powers", "PCA"],
    ),
    concept(
        "Spectral Theorem", "subtopic", "Linear Algebra",
        "The spectral theorem states that every real symmetric matrix is diagonalizable by an orthonormal basis of eigenvectors with real eigenvalues. "
        "It guarantees a clean eigendecomposition for symmetric matrices and underpins the theory of normal matrices. "
        "This result is foundational to PCA, quantum mechanics, and positive definite matrix analysis.",
        8, ["spectral theorem", "symmetric matrices", "orthonormal", "eigendecomposition", "PCA"],
    ),
    # Linear Transformations
    concept(
        "Kernel & Image", "subtopic", "Linear Algebra",
        "The kernel (null space) of a linear transformation is the set of all inputs mapped to zero, while the image (column space) is the set of all possible outputs. "
        "The rank-nullity theorem states the sum of dimensions of kernel and image equals the domain dimension. "
        "These subspaces characterize invertibility and output range of linear maps.",
        7, ["kernel", "image", "null space", "rank-nullity", "linear maps"],
    ),
    concept(
        "Change of Basis", "subtopic", "Linear Algebra",
        "A change of basis expresses vectors and linear maps relative to a different coordinate system, altering their matrix representations. "
        "The transformation uses an invertible change-of-basis matrix to convert between coordinate representations. "
        "Understanding change of basis is essential for diagonalization, orthogonal projections, and interpreting PCA.",
        6, ["basis", "coordinates", "matrix representation", "diagonalization", "projections"],
    ),
    concept(
        "Orthogonal Transformations", "subtopic", "Linear Algebra",
        "Orthogonal transformations are linear maps represented by orthogonal matrices that preserve distances and angles in Euclidean space. "
        "They include rotations and reflections, and their matrices satisfy Q^T Q = I. "
        "Orthogonal transformations are the symmetries of Euclidean geometry and appear in PCA, signal processing, and physics.",
        7, ["orthogonal", "rotations", "reflections", "isometry", "Euclidean"],
    ),
]

# ---------------------------------------------------------------------------
# Subtopics — Machine Learning
# ---------------------------------------------------------------------------

ML_SUBTOPICS = [
    # Supervised Learning
    concept(
        "Linear Regression", "subtopic", "Machine Learning",
        "Linear regression models a dependent variable as a linear function of independent variables, minimizing the sum of squared residuals. "
        "It provides closed-form solutions via normal equations or iterative solutions via gradient descent. "
        "Despite its simplicity, it serves as the foundation for understanding more complex regression models.",
        7, ["regression", "linear model", "least squares", "prediction", "coefficients"],
    ),
    concept(
        "Logistic Regression", "subtopic", "Machine Learning",
        "Logistic regression is a classification algorithm that models the probability of a binary outcome using the sigmoid function applied to a linear combination of features. "
        "It outputs calibrated probabilities and is trained by maximizing log-likelihood. "
        "It is widely used in medicine and finance as a strong baseline for classification tasks.",
        7, ["classification", "sigmoid", "probability", "log-likelihood", "binary"],
    ),
    concept(
        "Decision Trees", "subtopic", "Machine Learning",
        "A decision tree partitions the feature space into regions using a hierarchy of binary splits, predicting based on majority class or mean value in each region. "
        "Trees are trained greedily by selecting splits that maximize information gain or minimize impurity. "
        "They are interpretable and form the basis for ensemble methods like random forests.",
        7, ["decision trees", "splits", "information gain", "classification", "interpretable"],
    ),
    # Unsupervised Learning
    concept(
        "K-Means Clustering", "subtopic", "Machine Learning",
        "K-means partitions data into k clusters by iteratively assigning points to the nearest centroid and recomputing centroids as cluster means. "
        "The algorithm converges to a local minimum of the within-cluster sum of squared distances. "
        "It is computationally efficient but sensitive to initialization and the choice of k.",
        7, ["clustering", "centroids", "k-means", "unsupervised", "partitioning"],
    ),
    concept(
        "PCA (Dimensionality Reduction)", "subtopic", "Machine Learning",
        "Principal Component Analysis projects data onto directions of maximum variance, computed as eigenvectors of the data covariance matrix. "
        "By retaining only the top principal components, PCA reduces dimensionality while preserving the most variance. "
        "It is used for visualization, noise reduction, and feature extraction in machine learning pipelines.",
        8, ["PCA", "dimensionality reduction", "eigenvectors", "variance", "covariance"],
    ),
    concept(
        "Gaussian Mixture Models", "subtopic", "Machine Learning",
        "Gaussian Mixture Models represent a probability distribution as a weighted sum of Gaussian distributions, each representing a cluster. "
        "They are trained using the Expectation-Maximization algorithm, alternating between soft cluster assignments and parameter updates. "
        "GMMs provide a probabilistic generalization of k-means with richer cluster shapes.",
        6, ["GMM", "mixture models", "EM algorithm", "clustering", "Gaussian"],
    ),
    # Neural Networks
    concept(
        "Backpropagation", "subtopic", "Machine Learning",
        "Backpropagation computes gradients in neural networks by applying the chain rule recursively from the output layer back to the input layer. "
        "It efficiently computes the gradient of the loss with respect to every weight, enabling gradient descent. "
        "Without backpropagation, training deep networks would be computationally intractable.",
        9, ["backpropagation", "gradients", "chain rule", "neural networks", "training"],
    ),
    concept(
        "Activation Functions", "subtopic", "Machine Learning",
        "Activation functions introduce non-linearity into neural networks, enabling them to approximate complex functions. "
        "Common choices include ReLU, sigmoid, and tanh, differing in gradient flow, output range, and computational cost. "
        "The choice significantly affects training dynamics, vanishing gradient issues, and model expressiveness.",
        7, ["activation", "ReLU", "sigmoid", "non-linearity", "neural networks"],
    ),
    concept(
        "Gradient Descent", "subtopic", "Machine Learning",
        "Gradient descent is an iterative optimization algorithm that updates model parameters in the direction of the negative gradient to minimize a loss function. "
        "Variants include batch, stochastic, and mini-batch gradient descent, differing in data used per update. "
        "It is the foundational training algorithm for nearly all differentiable machine learning models.",
        9, ["gradient descent", "optimization", "learning rate", "convergence", "training"],
    ),
    # Model Evaluation
    concept(
        "Train/Test Split", "subtopic", "Machine Learning",
        "The train/test split divides a dataset into a training portion for fitting the model and a held-out portion for evaluating generalization. "
        "Proper splitting prevents data leakage and ensures the test set provides an unbiased performance estimate. "
        "The split ratio is typically 80/20 or 70/30 depending on dataset size.",
        6, ["train/test", "evaluation", "generalization", "data leakage", "holdout"],
    ),
    concept(
        "Cross-Validation", "subtopic", "Machine Learning",
        "Cross-validation evaluates model performance by repeatedly splitting data into training and validation folds and averaging results across splits. "
        "K-fold cross-validation provides more reliable generalization estimates than a single train/test split. "
        "It aids hyperparameter selection and model comparison when data is limited.",
        7, ["cross-validation", "k-fold", "generalization", "hyperparameters", "validation"],
    ),
    concept(
        "Precision, Recall & F1", "subtopic", "Machine Learning",
        "Precision measures the fraction of predicted positives that are truly positive, while recall measures the fraction of true positives that were identified. "
        "The F1 score is the harmonic mean of precision and recall, providing a single balanced metric. "
        "These are essential for evaluating classifiers under class imbalance where accuracy misleads.",
        7, ["precision", "recall", "F1", "classification", "imbalance"],
    ),
]

# ---------------------------------------------------------------------------
# Subtopics — Probability & Statistics
# ---------------------------------------------------------------------------

PS_SUBTOPICS = [
    # Probability Theory
    concept(
        "Conditional Probability", "subtopic", "Probability & Statistics",
        "Conditional probability P(A|B) quantifies the probability of event A given that event B has occurred, defined as P(A∩B)/P(B). "
        "It forms the basis for reasoning about dependencies between random events and updating beliefs with new information. "
        "Conditional probability is the cornerstone of Bayesian reasoning, graphical models, and causal inference.",
        8, ["conditional probability", "Bayes", "dependence", "events", "inference"],
    ),
    concept(
        "Bayes Theorem", "subtopic", "Probability & Statistics",
        "Bayes' theorem relates P(A|B) to its inverse P(B|A) through P(A|B) = P(B|A)P(A)/P(B). "
        "It provides the mathematical rule for updating beliefs about hypotheses given new evidence. "
        "Bayes' theorem is fundamental to probabilistic reasoning, spam filtering, medical diagnosis, and machine learning.",
        9, ["Bayes theorem", "posterior", "prior", "likelihood", "inference"],
    ),
    concept(
        "Independence", "subtopic", "Probability & Statistics",
        "Two events are independent if the occurrence of one does not affect the probability of the other, formally P(A∩B) = P(A)P(B). "
        "Independence simplifies probability computations dramatically and underlies the naive Bayes classifier. "
        "Distinguishing independence from correlation and causation is critical in statistical modeling.",
        7, ["independence", "probability", "correlation", "causation", "events"],
    ),
    # Random Variables
    concept(
        "Distributions & Expectation", "subtopic", "Probability & Statistics",
        "A probability distribution describes how probabilities are assigned to outcomes of a random variable via PMF or PDF. "
        "The expectation is the probability-weighted average of all possible values a random variable can take. "
        "Distributions and expectations are primary tools for characterizing random quantities in probability and statistics.",
        8, ["distributions", "expectation", "PMF", "PDF", "random variables"],
    ),
    concept(
        "Variance & Std Deviation", "subtopic", "Probability & Statistics",
        "Variance measures the expected squared deviation of a random variable from its mean, quantifying distributional spread. "
        "The standard deviation, its square root, is expressed in the same units and is more interpretable. "
        "These measures are essential for understanding uncertainty and constructing confidence intervals.",
        7, ["variance", "standard deviation", "spread", "mean", "uncertainty"],
    ),
    concept(
        "Central Limit Theorem", "subtopic", "Probability & Statistics",
        "The Central Limit Theorem states that the mean of many independent, identically distributed random variables converges to a normal distribution regardless of the original distribution. "
        "It justifies widespread use of normal approximations and z-tests in classical statistics. "
        "The CLT is one of the most profound results in probability, underpinning frequentist statistical inference.",
        9, ["CLT", "normal distribution", "convergence", "sampling", "statistics"],
    ),
    # Statistical Inference
    concept(
        "Hypothesis Testing", "subtopic", "Probability & Statistics",
        "Hypothesis testing decides between a null and alternative hypothesis based on observed data and a significance threshold. "
        "A test statistic is computed and compared to its null distribution to produce a p-value. "
        "It provides a formal framework for making decisions under uncertainty in scientific research.",
        8, ["hypothesis testing", "null hypothesis", "significance", "p-value", "statistics"],
    ),
    concept(
        "Confidence Intervals", "subtopic", "Probability & Statistics",
        "A confidence interval is a range of values computed from sample data expected to contain the true parameter with a specified probability. "
        "A 95% CI constructed by repeated sampling would contain the true parameter 95% of the time. "
        "Confidence intervals quantify estimation precision, providing more information than point estimates.",
        8, ["confidence intervals", "estimation", "uncertainty", "parameters", "statistics"],
    ),
    concept(
        "p-values", "subtopic", "Probability & Statistics",
        "A p-value is the probability of observing a test statistic at least as extreme as observed, assuming the null hypothesis is true. "
        "Small p-values provide evidence against the null hypothesis, with threshold α used for binary decisions. "
        "Misinterpretation is widespread; a p-value is not the probability that the null hypothesis is true.",
        7, ["p-value", "hypothesis testing", "significance", "null hypothesis", "statistics"],
    ),
    # Bayesian Statistics
    concept(
        "Prior & Posterior", "subtopic", "Probability & Statistics",
        "The prior distribution represents beliefs about a parameter before observing data, while the posterior represents updated beliefs after incorporating data via Bayes' theorem. "
        "The posterior is proportional to likelihood times prior, encapsulating all available information. "
        "Their interplay determines how much data are needed to overcome prior beliefs.",
        8, ["prior", "posterior", "Bayesian", "beliefs", "update"],
    ),
    concept(
        "Maximum Likelihood Estimation", "subtopic", "Probability & Statistics",
        "Maximum likelihood estimation finds parameter values that maximize the probability of the observed data under the assumed model. "
        "It is a principled estimation method with desirable asymptotic properties of consistency and efficiency. "
        "MLE underpins training of logistic regression, Gaussian models, and many machine learning algorithms.",
        8, ["MLE", "likelihood", "estimation", "parameters", "optimization"],
    ),
    concept(
        "Bayesian Inference", "subtopic", "Probability & Statistics",
        "Bayesian inference updates a prior distribution to a posterior using observed data and the likelihood function through Bayes' theorem. "
        "Unlike frequentist inference, it treats parameters as random variables and produces full posterior distributions. "
        "It enables coherent uncertainty quantification, hierarchical modeling, and principled decision-making.",
        9, ["Bayesian inference", "posterior", "uncertainty", "hierarchical", "probabilistic"],
    ),
]

# ---------------------------------------------------------------------------
# Subtopics — Calculus
# ---------------------------------------------------------------------------

CALC_SUBTOPICS = [
    # Differential Calculus
    concept(
        "Limits & Continuity", "subtopic", "Calculus",
        "A limit describes the value a function approaches as its input approaches a point, formalizing proximity without necessarily reaching the point. "
        "Continuity requires the limit equals the function value, ensuring no breaks or jumps. "
        "These concepts are the rigorous foundation of calculus enabling precise definitions of derivatives and integrals.",
        7, ["limits", "continuity", "epsilon-delta", "analysis", "functions"],
    ),
    concept(
        "Chain Rule", "subtopic", "Calculus",
        "The chain rule is the fundamental differentiation rule for composite functions: the derivative of f(g(x)) is f′(g(x))·g′(x). "
        "It enables differentiation of arbitrarily complex compositions by breaking them into simpler parts. "
        "In machine learning, the chain rule applied recursively across network layers is the mathematical basis of backpropagation.",
        8, ["chain rule", "composite functions", "differentiation", "backpropagation", "calculus"],
    ),
    concept(
        "Partial Derivatives", "subtopic", "Calculus",
        "A partial derivative measures the rate of change of a multivariable function with respect to one variable while holding others constant. "
        "Computing partial derivatives for all variables yields the gradient vector pointing in the direction of steepest ascent. "
        "Partial derivatives are essential for optimization in multiple dimensions including training machine learning models.",
        8, ["partial derivatives", "gradient", "multivariable", "optimization", "calculus"],
    ),
    # Integral Calculus
    concept(
        "Definite & Indefinite Integrals", "subtopic", "Calculus",
        "An indefinite integral is an antiderivative representing a family of functions differing by a constant. "
        "A definite integral is the net signed area under a curve over an interval, computed as the limit of Riemann sums. "
        "Both types are unified by the Fundamental Theorem of Calculus.",
        7, ["integrals", "antiderivative", "area", "Riemann sums", "calculus"],
    ),
    concept(
        "Integration by Parts", "subtopic", "Calculus",
        "Integration by parts is derived from the product rule of differentiation, given by ∫u dv = uv − ∫v du. "
        "It transforms integrals of products of functions into potentially simpler forms by strategically assigning terms. "
        "This technique integrates polynomials times exponentials, logarithms, and trigonometric expressions.",
        6, ["integration by parts", "product rule", "antiderivative", "technique", "calculus"],
    ),
    concept(
        "Fundamental Theorem of Calculus", "subtopic", "Calculus",
        "The Fundamental Theorem of Calculus establishes that differentiation and integration are inverse operations by linking definite integrals to antiderivatives. "
        "The first part states the derivative of the integral from a to x is f(x); the second allows definite integrals to be computed via antiderivatives. "
        "This theorem unifies differential and integral calculus.",
        9, ["fundamental theorem", "integration", "differentiation", "antiderivatives", "calculus"],
    ),
    # Multivariable Calculus
    concept(
        "Gradient & Directional Derivatives", "subtopic", "Calculus",
        "The gradient of a scalar function is the vector of partial derivatives, pointing in the direction of steepest increase. "
        "A directional derivative measures the rate of change in any specified direction, computed as the dot product of the gradient and the unit direction vector. "
        "Gradients are central to multivariable optimization and machine learning.",
        9, ["gradient", "directional derivatives", "partial derivatives", "optimization", "machine learning"],
    ),
    concept(
        "Jacobian Matrix", "subtopic", "Calculus",
        "The Jacobian matrix of a vector-valued function contains all first-order partial derivatives, with entry (i,j) being the partial of output i with respect to input j. "
        "It generalizes the derivative to vector-to-vector mappings and describes the local linear approximation. "
        "The Jacobian determinant measures local volume scaling and appears in change-of-variables formulas.",
        7, ["Jacobian", "partial derivatives", "vector functions", "linearization", "volume"],
    ),
    concept(
        "Lagrange Multipliers", "subtopic", "Calculus",
        "The method of Lagrange multipliers finds extrema of a function subject to equality constraints by introducing auxiliary multiplier variables. "
        "At a constrained optimum, the gradient of the objective is a linear combination of the constraint gradients. "
        "This technique is fundamental to constrained optimization in mathematics, economics, and machine learning regularization.",
        8, ["Lagrange multipliers", "constrained optimization", "constraints", "KKT", "regularization"],
    ),
    # Optimization
    concept(
        "Convex Functions", "subtopic", "Calculus",
        "A convex function satisfies f(λx + (1−λ)y) ≤ λf(x) + (1−λ)f(y), meaning the chord between any two graph points lies above it. "
        "Convexity guarantees any local minimum is a global minimum, making optimization tractable. "
        "Identifying and exploiting convexity is central to optimization theory and well-behaved loss function design.",
        8, ["convexity", "global minimum", "optimization", "loss functions", "machine learning"],
    ),
    concept(
        "Saddle Points", "subtopic", "Calculus",
        "A saddle point is a critical point where the gradient is zero but it is neither a local minimum nor maximum. "
        "Saddle points are prevalent in high-dimensional parameter spaces of neural networks and can slow gradient descent. "
        "Understanding their geometry is important for designing effective optimization algorithms.",
        7, ["saddle points", "critical points", "optimization", "neural networks", "gradient"],
    ),
    concept(
        "Gradient Descent (Numerical)", "subtopic", "Calculus",
        "Gradient descent is a first-order iterative optimization algorithm that subtracts a step size times the gradient from the current parameter vector. "
        "Starting from an initial point, it follows steepest descent toward a local minimum. "
        "The learning rate critically affects convergence speed and stability, making it an active area of numerical optimization research.",
        8, ["gradient descent", "optimization", "learning rate", "convergence", "numerical methods"],
    ),
]

# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

DOCUMENTS = [
    document("linear_algebra_notes.pdf", "Linear Algebra", 12),
    document("ml_textbook_ch1_3.pdf", "Machine Learning", 28),
    document("ml_lab_exercises.pdf", "Machine Learning", 8),
    document("prob_stats_summary.pdf", "Probability & Statistics", 15),
    document("calculus_exam_prep.pdf", "Calculus", 9),
]

ALL_CONCEPTS = (
    SUBJECTS
    + LA_TOPICS + ML_TOPICS + PS_TOPICS + CALC_TOPICS
    + LA_SUBTOPICS + ML_SUBTOPICS + PS_SUBTOPICS + CALC_SUBTOPICS
)


def _set_parents() -> None:
    """Populate the parent field on every concept to match the app's data model."""
    # Topics: parent = the subject name they belong to
    for c in LA_TOPICS + ML_TOPICS + PS_TOPICS + CALC_TOPICS:
        c["parent"] = c["subject"]

    # Subtopics: parent = immediate parent topic name
    topic_subtopics = {
        "Vector Spaces":              ["Basis & Dimension", "Span and Linear Independence", "Subspaces"],
        "Matrix Operations":          ["Matrix Multiplication", "Determinants", "Inverse Matrices"],
        "Eigenvalues & Eigenvectors": ["Characteristic Polynomial", "Diagonalization", "Spectral Theorem"],
        "Linear Transformations":     ["Kernel & Image", "Change of Basis", "Orthogonal Transformations"],
        "Supervised Learning":        ["Linear Regression", "Logistic Regression", "Decision Trees"],
        "Unsupervised Learning":      ["K-Means Clustering", "PCA (Dimensionality Reduction)", "Gaussian Mixture Models"],
        "Neural Networks":            ["Backpropagation", "Activation Functions", "Gradient Descent"],
        "Model Evaluation":           ["Train/Test Split", "Cross-Validation", "Precision, Recall & F1"],
        "Probability Theory":         ["Conditional Probability", "Bayes Theorem", "Independence"],
        "Random Variables":           ["Distributions & Expectation", "Variance & Std Deviation", "Central Limit Theorem"],
        "Statistical Inference":      ["Hypothesis Testing", "Confidence Intervals", "p-values"],
        "Bayesian Statistics":        ["Prior & Posterior", "Maximum Likelihood Estimation", "Bayesian Inference"],
        "Differential Calculus":      ["Limits & Continuity", "Chain Rule", "Partial Derivatives"],
        "Integral Calculus":          ["Definite & Indefinite Integrals", "Integration by Parts", "Fundamental Theorem of Calculus"],
        "Multivariable Calculus":     ["Gradient & Directional Derivatives", "Jacobian Matrix", "Lagrange Multipliers"],
        "Optimization":               ["Convex Functions", "Saddle Points", "Gradient Descent (Numerical)"],
    }
    for topic_name, subtopic_names in topic_subtopics.items():
        for sname in subtopic_names:
            concepts_by_name[sname]["parent"] = topic_name


_set_parents()

# ---------------------------------------------------------------------------
# Relationship builders
# ---------------------------------------------------------------------------

def _build_hierarchical_rels() -> list[dict]:
    rels = []

    subject_topics = {
        "Linear Algebra":           LA_TOPICS,
        "Machine Learning":         ML_TOPICS,
        "Probability & Statistics": PS_TOPICS,
        "Calculus":                 CALC_TOPICS,
    }
    for subj in SUBJECTS:
        for topic in subject_topics[subj["name"]]:
            rels.append({"from_id": subj["id"], "to_id": topic["id"], "rel_type": "hierarchical", "cross_subject": False, "weight": 1.0})

    topic_subtopics = {
        "Vector Spaces":            ["Basis & Dimension", "Span and Linear Independence", "Subspaces"],
        "Matrix Operations":        ["Matrix Multiplication", "Determinants", "Inverse Matrices"],
        "Eigenvalues & Eigenvectors": ["Characteristic Polynomial", "Diagonalization", "Spectral Theorem"],
        "Linear Transformations":   ["Kernel & Image", "Change of Basis", "Orthogonal Transformations"],
        "Supervised Learning":      ["Linear Regression", "Logistic Regression", "Decision Trees"],
        "Unsupervised Learning":    ["K-Means Clustering", "PCA (Dimensionality Reduction)", "Gaussian Mixture Models"],
        "Neural Networks":          ["Backpropagation", "Activation Functions", "Gradient Descent"],
        "Model Evaluation":         ["Train/Test Split", "Cross-Validation", "Precision, Recall & F1"],
        "Probability Theory":       ["Conditional Probability", "Bayes Theorem", "Independence"],
        "Random Variables":         ["Distributions & Expectation", "Variance & Std Deviation", "Central Limit Theorem"],
        "Statistical Inference":    ["Hypothesis Testing", "Confidence Intervals", "p-values"],
        "Bayesian Statistics":      ["Prior & Posterior", "Maximum Likelihood Estimation", "Bayesian Inference"],
        "Differential Calculus":    ["Limits & Continuity", "Chain Rule", "Partial Derivatives"],
        "Integral Calculus":        ["Definite & Indefinite Integrals", "Integration by Parts", "Fundamental Theorem of Calculus"],
        "Multivariable Calculus":   ["Gradient & Directional Derivatives", "Jacobian Matrix", "Lagrange Multipliers"],
        "Optimization":             ["Convex Functions", "Saddle Points", "Gradient Descent (Numerical)"],
    }
    for topic_name, subtopic_names in topic_subtopics.items():
        tid = concepts_by_name[topic_name]["id"]
        for sname in subtopic_names:
            rels.append({"from_id": tid, "to_id": concepts_by_name[sname]["id"], "rel_type": "hierarchical", "cross_subject": False, "weight": 1.0})

    return rels


def _build_cross_rels() -> list[dict]:
    cn = concepts_by_name
    rows = [
        ("Linear Algebra",                   "Machine Learning",               "cross_subject", 0.95),
        ("Probability & Statistics",          "Machine Learning",               "cross_subject", 0.92),
        ("Calculus",                          "Machine Learning",               "cross_subject", 0.90),
        ("Calculus",                          "Linear Algebra",                 "cross_subject", 0.85),
        ("Eigenvalues & Eigenvectors",        "PCA (Dimensionality Reduction)", "cross_subject", 0.97),
        ("Matrix Operations",                 "Neural Networks",                "cross_subject", 0.93),
        ("Gradient Descent",                  "Gradient Descent (Numerical)",   "cross_subject", 0.99),
        ("Backpropagation",                   "Chain Rule",                     "cross_subject", 0.96),
        ("Bayes Theorem",                     "Bayesian Statistics",            "cross_subject", 0.98),
        ("Bayes Theorem",                     "Bayesian Inference",             "cross_subject", 0.95),
        ("Conditional Probability",           "Bayes Theorem",                  "prerequisite",  0.90),
        ("Linear Regression",                 "Gradient Descent",               "prerequisite",  0.88),
        ("Eigenvalues & Eigenvectors",        "Spectral Theorem",               "prerequisite",  0.91),
        ("Gradient & Directional Derivatives","Gradient Descent",               "cross_subject", 0.94),
        ("Distributions & Expectation",       "Gaussian Mixture Models",        "cross_subject", 0.89),
        ("Central Limit Theorem",             "Confidence Intervals",           "cross_subject", 0.87),
        ("Hypothesis Testing",                "Cross-Validation",               "related",       0.72),
        ("Diagonalization",                   "PCA (Dimensionality Reduction)", "cross_subject", 0.91),
        ("Lagrange Multipliers",              "Optimization",                   "hierarchical",  0.85),
        ("Logistic Regression",               "Probability Theory",             "cross_subject", 0.86),
    ]
    return [
        {"from_id": cn[f]["id"], "to_id": cn[t]["id"], "rel_type": tp, "cross_subject": tp == "cross_subject", "weight": w}
        for f, t, tp, w in rows
    ]


def _build_contains_rels() -> list[dict]:
    # App model: (Document)-[:CONTAINS]->(Concept)
    # Assign every concept to one document based on its subject.
    # ML has two documents; split topics/subtopics between them.
    la_doc   = next(d for d in DOCUMENTS if d["filename"] == "linear_algebra_notes.pdf")
    ml_main  = next(d for d in DOCUMENTS if d["filename"] == "ml_textbook_ch1_3.pdf")
    ml_lab   = next(d for d in DOCUMENTS if d["filename"] == "ml_lab_exercises.pdf")
    ps_doc   = next(d for d in DOCUMENTS if d["filename"] == "prob_stats_summary.pdf")
    calc_doc = next(d for d in DOCUMENTS if d["filename"] == "calculus_exam_prep.pdf")

    # ML split: textbook gets subject + Supervised + Neural Networks + Model Evaluation (and their subtopics)
    #           lab gets Unsupervised Learning (and its subtopics)
    ml_lab_names = {
        "Unsupervised Learning", "K-Means Clustering", "PCA (Dimensionality Reduction)",
        "Gaussian Mixture Models",
    }

    rels = []
    for c in ALL_CONCEPTS:
        subj = c["subject"]
        if subj == "Linear Algebra":
            doc = la_doc
        elif subj == "Machine Learning":
            doc = ml_lab if c["name"] in ml_lab_names else ml_main
        elif subj == "Probability & Statistics":
            doc = ps_doc
        else:
            doc = calc_doc
        rels.append({"doc_id": doc["id"], "concept_id": c["id"]})
    return rels


# ---------------------------------------------------------------------------
# Main seeding function
# ---------------------------------------------------------------------------

def seed(driver):
    with driver.session() as session:
        # Cleanup
        session.run("MATCH (u:User {user_id: $uid}) DETACH DELETE u", uid=USER_ID)
        session.run("MATCH (n:Concept {user_id: $uid}) DETACH DELETE n", uid=USER_ID)
        session.run("MATCH (n:Document {user_id: $uid}) DETACH DELETE n", uid=USER_ID)

        # 1. User
        session.run(
            "CREATE (:User {user_id: $user_id, name: $name, created_at: $created_at})",
            user_id=USER_ID, name="Seed Student", created_at=NOW,
        )

        # 2. Documents
        session.run("UNWIND $docs AS d CREATE (n:Document) SET n = d", docs=DOCUMENTS)

        # 3. Concepts
        session.run("UNWIND $concepts AS c CREATE (n:Concept) SET n = c", concepts=ALL_CONCEPTS)

        # 4. OWNS
        session.run(
            "MATCH (u:User {user_id: $uid}) "
            "MATCH (d:Document {user_id: $uid}) "
            "CREATE (u)-[:OWNS]->(d)",
            uid=USER_ID,
        )

        # 5. CONTAINS  — direction: Document -[:CONTAINS]-> Concept
        session.run(
            "UNWIND $rels AS r "
            "MATCH (d:Document {id: r.doc_id}) "
            "MATCH (c:Concept {id: r.concept_id}) "
            "CREATE (d)-[:CONTAINS]->(c)",
            rels=_build_contains_rels(),
        )

        # 6. RELATED_TO
        all_rels = _build_hierarchical_rels() + _build_cross_rels()
        session.run(
            "UNWIND $rels AS r "
            "MATCH (a:Concept {id: r.from_id}) "
            "MATCH (b:Concept {id: r.to_id}) "
            "CREATE (a)-[:RELATED_TO {rel_type: r.rel_type, cross_subject: r.cross_subject, weight: r.weight}]->(b)",
            rels=all_rels,
        )

        # Verification
        doc_count = session.run(
            "MATCH (d:Document {user_id: $uid}) RETURN count(d) AS n", uid=USER_ID
        ).single()["n"]

        level_rows = session.run(
            "MATCH (c:Concept {user_id: $uid}) RETURN c.level AS level, count(c) AS n",
            uid=USER_ID,
        ).data()
        lc = {r["level"]: r["n"] for r in level_rows}

        rel_rows = session.run(
            "MATCH (a:Concept {user_id: $uid})-[r:RELATED_TO]->(:Concept) "
            "RETURN r.type AS type, count(r) AS n",
            uid=USER_ID,
        ).data()
        rc = {r["type"]: r["n"] for r in rel_rows}

        contains_count = session.run(
            "MATCH (:Document {user_id: $uid})-[:CONTAINS]->(:Concept) RETURN count(*) AS n",
            uid=USER_ID,
        ).single()["n"]

        owns_count = session.run(
            "MATCH (:User {user_id: $uid})-[:OWNS]->(:Document) RETURN count(*) AS n",
            uid=USER_ID,
        ).single()["n"]

        print(f"✓ User created: {USER_ID}")
        print(f"✓ Documents: {doc_count}")
        print(
            f"✓ Concepts: {lc.get('subject', 0)} subjects, "
            f"{lc.get('topic', 0)} topics, "
            f"{lc.get('subtopic', 0)} subtopics"
        )
        print(
            f"✓ RELATED_TO relationships: "
            f"hierarchical={rc.get('hierarchical', 0)}, "
            f"prerequisite={rc.get('prerequisite', 0)}, "
            f"related={rc.get('related', 0)}, "
            f"cross_subject={rc.get('cross_subject', 0)}"
        )
        print(f"✓ CONTAINS relationships: {contains_count}")
        print(f"✓ OWNS relationships: {owns_count}")


if __name__ == "__main__":
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        seed(driver)
    finally:
        driver.close()
