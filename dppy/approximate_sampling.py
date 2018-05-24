import time
import numpy as np

from cvxopt import matrix, spmatrix, solvers
solvers.options['show_progress'] = False
solvers.options['glpk'] = dict(msg_lev='GLP_MSG_OFF')

###############################################################
############## Approximate samplers for projection DPPs #######
###############################################################

def add_exchange_delete_sampler(kernel, nb_it_max = 10, T_max=10):
	""" MCMC sampler for generic DPPs, it is a mix of add/delete and basis exchange MCMC samplers.

	:param kernel:
			Kernel martrix
	:type kernel:
			array_type

	# :param s_init:
	# 		Initial sample.
	# :type s_init: 
	# 		list

	:param nb_it_max:
		Maximum number of iterations performed by the the algorithm.
		Default is 10.
	:type nb_it_max: 
		int

	:param T_max: 
		Maximum running time of the algorithm (in seconds).
		Default is 10s.
	:type T_max: 
			float

	:return:
		list of `nb_it_max` approximate samples of DPP(kernel)
	:rtype:
		array_type

	.. seealso::
			
			Algorithm 3 in :cite:`LiJeSr16c`
	"""

	# Initialization
	N = kernel.shape[0]
	ground_set = np.arange(N)

	# Build the initial sample
	nb_init_max = 100
	for _ in range(nb_init_max):
		r0 = np.random.choice(2*N, size=N, replace=False)
		S0 = np.intersect1d(s_init, ground_set)
		det_S0 = np.linalg.det(K[np.ix_(S0, S0)])
		if det_S0 > 1e-8:
			break
	else:
		raise ValueError("Problem of initilization!")

	sampl_size = len(S0) # Size of the current
	samples = [S0] # Initialize the collection (list) of samples
	
	# Evaluate running time...
	flag = True
	it, t_start = 1, time.time()

	while flag:

		S1 = S0.copy() # S1 = S0
		s = np.random.choice(sampl_size, size=1) # Uniform s in S_0 by index
		t = np.random.choice(np.delete(ground_set, S0), size=1) # Unif t in [N]-S_0

		unif_01 = np.random.rand() 
		ratio = sampl_size/N # Proportion of items in current sample

		# Add: S1 = S0 + t
		if unif_01 < 0.5*(1-ratio)**2:
			S1.append(t) # S1 = S0 + t
			# Accept_reject the move
			det_S1 = np.linalg.det(K[np.ix_(S1, S1)]) # det K_S1
			if np.random.rand() < (det_S1/det_S0 * (sampl_size+1)/(N-sampl_size)):
				S0, det_S0 = S1, det_S1
				samples.append(S1)
				sampl_size += 1

		# Exchange: S1 = S0 - s + t
		elif (0.5*(1-ratio)**2 <= unif_01) & (unif_01 < 0.5*(1-ratio)):
			del S1[s] # S1 = S0 - s
			S1.append(t) # S1 = S1 + t = S0 - s + t
			# Accept_reject the move
			det_S1 = np.linalg.det(K[np.ix_(S1, S1)]) # det K_S1
			if np.random.rand() < (det_S1/det_S0):
				S0, det_S0 = S1, det_S1
				samples.append(S1)
				# sampl_size stays the same

		# Delete: S1 = S0 - s
		elif (0.5*(1-ratio) <= unif_01) & (unif_01 < 0.5*(ratio**2+(1-ratio))):
			del S1[s] # S0 - s
			# Accept_reject the move
			det_S1 = np.linalg.det(K[np.ix_(S1, S1)]) # det K_S1
			if np.random.rand() < (det_S1/det_S0 * sampl_size/(N-(sampl_size-1))):
				S0, det_S0 = S1, det_S1
				samples.append(S1)
				sampl_size -= 1

		else:
			samples.append(S0)
		
		if nb_it_max:
			it += 1
			flag = it < nb_it_max
		elif T_max:
			flag = (time.time()-t_start) < T_max

	return samples

def add_delete_sampler(kernel, s_init, nb_it_max = 10, T_max=10):
	""" MCMC sampler for generic DPP(kernel), it performs local moves by removing/adding one element at a time.

	:param kernel:
			Kernel martrix
	:type kernel:
			array_type

	:param s_init:
			Initial sample.
	:type s_init: 
			list

	:param nb_it_max:
			Maximum number of iterations performed by the the algorithm.
			Default is 10.
	:type nb_it_max: 
			int

	:param T_max: 
			Maximum running time of the algorithm (in seconds).
			Default is 10s.
	:type T_max: 
			float

	:return:
		list of `nb_it_max` approximate samples of DPP(kernel)
	:rtype:
		array_type

	.. seealso::
			
			Algorithm 1 in :cite:`LiJeSr16c`
	"""

	# Initialization
	N = kernel.shape[0] # Number of elements

	S0 = s_init # Initial sample
	det_S0 = np.linalg.det(K[np.ix_(S0, S0)]) # det K_S0

	samples = [S0] # Initialize the collection (list) of samples
	
	# Evaluate running time...
	flag = True
	it, t_start = 1, time.time()

	while flag:

		# With proba 1/2 try to add/delete an element
		if np.random.rand() < 0.5: 

			# Perform the potential add/delete move S1 = S0 +/- s
			S1 = S0.copy() # S1 = S0
			s = np.random.choice(N, size=1) # Uniform item in [N]
			if s in S0: 
				S1.remove(s) # S1 = S0 - s
			else: 
				S1.append(s) # S1 = SO + s

			# Accept_reject the move
			det_S1 = np.linalg.det(K[np.ix_(S1, S1)]) # det K_S1
			if np.random.rand() < det_S1/det_S0:
				S0, det_S0 = S1, det_S1
				samples.append(S1)

			else:
				samples.append(S0)

		else:
			samples.append(S0)
		
		if nb_it_max:
			it += 1
			flag = it < nb_it_max
		elif T_max:
			flag = (time.time()-t_start) < T_max

	return samples

def basis_exchange_sampler(kernel, s_init, nb_it_max = 10, T_max=10):
	""" MCMC sampler for projection DPPs, based on the basis exchange property.

	:param kernel:
			Feature vector matrix, feature vectors are stacked columnwise.
			It is assumed to be full row rank.
	:type kernel:
			array_type

	:param s_init:
			Initial sample.
	:type s_init: 
			list

	:param nb_it_max:
			Maximum number of iterations performed by the the algorithm.
			Default is 10.
	:type nb_it_max: 
			int

	:param T_max: 
			Maximum running time of the algorithm (in seconds).
			Default is 10s.
	:type T_max: 
			float

	:return:
			MCMC chain of approximate samples (stacked row_wise i.e. nb_it_max rows).
	:rtype: 
			array_type

	.. seealso::
			
			Algorithm 2 in :cite:`LiJeSr16c`
	"""

	# Initialization
	N = kernel.shape[0] # Number of elements
	ground_set = np.arange(N) # Ground set

	k = len(s_init) # Size of the samples (only exchange: cardinality is fixed)
	S0 = s_init # Initial sample
	det_S0 = np.linalg.det(K[np.ix_(S0, S0)]) # det K_S0

	samples = [S0] # Initialize the collection (list) of samples
	
	# Evaluate running time...
	flag = True
	it, t_start = 1, time.time()

	while flag:

		# With proba 1/2 try to swap 2 elements
		if np.random.rand() < 0.5: 

			# Perform the potential exchange move S1 = S0 - s + t
			S1 = S0.copy() # S1 = S0
			rnd_ind = np.random.choice(k, size=1) # Uniform element of S_0 by index
			t = np.random.choice(np.delete(ground_set, S0), size=1) # t in [N]\S_0
			S1[rnd_ind] = t # S_1 = S_0 - S_0[rnd_ind] + t
			
			det_S1 = np.linalg.det(K[np.ix_(S1, S1)]) # det K_S1

			# Accept_reject the move w. proba
			if np.random.rand() < det_S1/det_S0:
				S0, det_S0 = S1, det_S1
				samples.append(S1)

			else: # if reject, stay in the same state
				samples.append(S0)	

		else:
			samples.append(S0)

		
		if nb_it_max:
			it += 1
			flag = it < nb_it_max
		elif T_max:
			flag = (time.time()-t_start) < T_max

	return samples




######################
###### ZONOTOPE ######
######################

def extract_basis(y_sol, eps=1e-5):
	""" Subroutine of zono_sampling to extract the tile of the zonotope 
	in which a point lies. It extracts the indices of entries of the solution 
	of LP :eq:`Px` that are in (0,1).

	:param y_sol: 
			Optimal solution of LP :eq:`Px`
	:type y_sol: 
			list
					
	:param eps: 
			Tolerance :math:`y_i^* \in (\epsilon, 1-\epsilon), \quad \epsilon \geq 0`
	:eps type: 
			float

	:return: 
			Indices of the feature vectors spanning the tile in which the point is lies. 
			:math:`B_{x} = \left\{ i \, ; \, y_i^* \in (0,1) \\right\}`
	:rtype: 
			list         
					
	.. seealso::

			Algorithm 3 in :cite:`GaBaVa17`

			- :func:`zono_sampling <zono_sampling>`
	"""

	basis = np.where((eps<y_sol)&(y_sol<1-eps))[0]
	
	return basis.tolist()

def zono_sampling(Vectors, c=None, nb_it_max = 10, T_max=10):
	""" MCMC based sampler for projection DPPs.
	The similarity matrix is the orthogonal projection matrix onto 
	the row span of the feature vector matrix.
	Samples are of size equal to the rank of the projection matrix 
	also equal to the rank of the feature matrix (assumed to be full row rank).

	:param Vectors:
			Feature vector matrix, feature vectors are stacked columnwise.
			It is assumed to be full row rank.
	:type Vectors:
			array_type

	:param c: Linear objective of the linear program used to identify 
			the tile in which a point lies.
	:type c: list

	:param nb_it_max:
			Maximum number of iterations performed by the the algorithm.
			Default is 10.
	:type nb_it_max: 
			int

	:param T_max: 
			Maximum running time of the algorithm (in seconds).
			Default is 10s.
	:type T_max: 
			float

	:return:
			MCMC chain of approximate samples (stacked row_wise i.e. nb_it_max rows).
	:rtype: 
			array_type    

	.. seealso::

			Algorithm 5 in :cite:`GaBaVa17`

			- :func:`extract_basis <extract_basis>`
			- :func:`basis_exchange <basis_exchange>`
	"""

	r,n = Vectors.shape

	#################################################
	############### Linear problems #################
	#################################################
	# Canonical form
	# min		c.T*x 				min		c.T*x
	# s.t.	G*x <= h	<=> s.t.	G*x + s = h
	#				A*x = b 						A*x = b
	#														s >= 0
	# CVXOPT
	# =====> solvers.lp(c, G, h, A, b, solver='glpk')
	#################################################

	### To access the tile Z(B_x) 
	# Solve P_x(A,c)
	#########################################################
	# y^* =
	# argmin  c.T*y       argmin  c.T*y
	# s.t.		A*y = x 		<=> s.t.    	A  *y  =	x
	#					0 <= y <= 1						[ I_n] *y <=	[1^n]
	#																[-I_n]				[0^n]
	#########################################################
	# Then B_x = \{ i ; y_i^* \in ]0,1[ \}
	if c is None:
		c = matrix(np.random.randn(n))

	A = spmatrix(0.0, [], [], (r, n))
	A[:,:] = Vectors

	G = spmatrix(0.0, [], [], (2*n, n))
	G[:n,:] = spmatrix(1.0, range(n), range(n))
	G[n:,:] = spmatrix(-1.0, range(n), range(n))

	### Endpoints of segment 
	# D_x \cap Z(A) = [x+alpha_m*d, x-alpha_M*d]
	#############################################################################################
	# alpha_m/_M = 
	# argmin  +/-alpha 									argmin  [+/-1 0^n].T * [alpha,lambda]
	# s.t.    x + alpha d = A lambda  <=>   s.t.  [-d A] * [alpha,lambda] = x
	#					0 <= lambda <= 1            [ 0^n I_n ] *[alpha,lambda] <=  [1^n]
	#																			[ 0^n -I_n]             				[0^n]
	#############################################################################################

	c_mM = matrix(0.0, (n+1,1))
	c_mM[0] = 1.0

	A_mM = spmatrix(0.0, [], [], (r, n+1))
	A_mM[:,1:] = A

	G_mM = spmatrix(0.0, [], [], (2*n, n+1))
	G_mM[:,1:] = G

	# Common h to both kind of LP
	# cf. 0 <= y <= 1 and 0 <= lambda <= 1
	h = matrix(0.0, (2*n, 1))
	h[:n,:] = 1.0

	########################
	#### Initialization ####
	########################
	B_x0 = []
	while len(B_x0) != r:
		# Initial point x0 = A*u, u~U[0,1]^n
		x0 = matrix(Vectors.dot(np.random.rand(n)))
		# Initial tile B_x0
				# Solve P_x0(A,c)
		y_star = solvers.lp(c, G, h, A, x0, solver='glpk')['x']
				# Get the tile
		B_x0 = extract_basis(np.asarray(y_star))

	# Initialize sequence of samples
	Bases = [B_x0]

	# Compute the det of the tile (Vol(B)=abs(det(B)))
	det_B_x0 = np.linalg.det(Vectors[:,B_x0])

	it, t_start = 1, time.time()
	flag = it < nb_it_max
	while flag:

		# Take uniform direction d defining D_x0
		d = matrix(np.random.randn(r,1))

		# Define D_x0 \cap Z(A) = [x0 + alpha_m*d, x0 - alpha_M*d]
			# Update the constraint [-d A] * [alpha,lambda] = x
		A_mM[:,0] = -d
				# Find alpha_m/M
		alpha_m = solvers.lp(c_mM, G_mM, h, A_mM, x0, solver='glpk')['x'][0]
		alpha_M = solvers.lp(-c_mM, G_mM, h, A_mM, x0, solver='glpk')['x'][0]

		# Propose x1 ~ U_{[x0+alpha_m*d, x0-alpha_M*d]}
		x1 = x0 + (alpha_m + (alpha_M-alpha_m)*np.random.rand())*d
		# Proposed tile B_x1
			# Solve P_x1(A,c)
		y_star = solvers.lp(c, G, h, A, x1, solver='glpk')['x']
				# Get the tile
		B_x1 = extract_basis(np.asarray(y_star))

		# Accept/Reject the move with proba Vol(B1)/Vol(B0)
		if len(B_x1) != r: # In case extract_basis returned smtg ill conditioned
			Bases.append(B_x0)
		else:
			det_B_x1 = np.linalg.det(Vectors[:,B_x1])
			if np.random.rand() < abs(det_B_x1/det_B_x0):
					x0, B_x0, det_B_x0 = x1, B_x1, det_B_x1
					Bases.append(B_x1)
			else:
					Bases.append(B_x0)

		if nb_it_max is not None:
			it += 1
			flag = it < nb_it_max
		elif T_max:
			flag = (time.time() - t_start) < T_max

		print("Time enlapsed", time.time()-t_start)

	return np.array(Bases)