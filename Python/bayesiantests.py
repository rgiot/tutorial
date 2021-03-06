import numpy as np
import numpy.matlib

LEFT, ROPE, RIGHT = range(3)

## SIGN TEST
def signtest_MC(x, rope, prior_strength=1, prior_place=ROPE, nsamples=50000):
    """
    Args:
        x (array): a vector of differences or a 2d array with pairs of scores.
        rope (float): the width of the rope  
        prior_strength (float): prior strength (default: 1)
        prior_place (LEFT, ROPE or RIGHT): the region to which the prior is
            assigned (default: ROPE)
        nsamples (int): the number of Monte Carlo samples
    
    Returns:
        2-d array with rows corresponding to samples and columns to
        probabilities `[p_left, p_rope, p_right]`
    """
    if prior_strength < 0:
        raise ValueError('Prior strength must be nonegative')
    if nsamples < 0:
        raise ValueError('Number of samples must be a positive integer')
    if rope < 0:
        raise ValueError('Rope must be a positive number')
 
    if x.ndim == 2:
        x = x[:, 1] - x[:, 0]
    nleft = sum(x < -rope)
    nright = sum(x > rope)
    nrope = len(x) - nleft - nright
    alpha = np.array([nleft, nrope, nright], dtype=float)
    alpha += 0.0001  # for numerical stability
    alpha[prior_place] += prior_strength
    return np.random.dirichlet(alpha, nsamples)

def signtest(x, rope, prior_strength=1, prior_place=ROPE, nsamples=50000,
             verbose=False, names=('C1', 'C2')):
    """
    Args:
        x (array): a vector of differences or a 2d array with pairs of scores.
        rope (float): the width of the rope  
        prior_strength (float): prior strength (default: 1)
        prior_place (LEFT, ROPE or RIGHT): the region to which the prior is
            assigned (default: ROPE)
        nsamples (int): the number of Monte Carlo samples
        verbose (bool): report the computed probabilities
        names (pair of str): the names of the two classifiers

    Returns:
        p_left, p_rope, p_right 
    """
    samples = signtest_MC(x, rope, prior_strength, prior_place, nsamples)
    
    winners = np.argmax(samples, axis=1)
    pl, pe, pr = np.bincount(winners, minlength=3) / len(winners)
    if verbose:
        print('P({c1} > {c2}) = {pl}, P(rope) = {pe}, P({c2} > {c1}) = {pr}'.
              format(c1=names[0], c2=names[1], pl=pl, pe=pe, pr=pr))
    return pl, pe, pr

## SIGNEDRANK
def heaviside(X):
    Y = np.zeros(X.shape);
    Y[np.where(X  > 0)] = 1;
    Y[np.where(X == 0)] = 0.5;
    return Y #1 * (x > 0)

def signrank_MC(x, rope, prior_strength=0.6, prior_place=ROPE, nsamples=50000):
    """
    Args:
        x (array): a vector of differences or a 2d array with pairs of scores.
        rope (float): the width of the rope  
        prior_strength (float): prior strength (default: 0.6)
        prior_place (LEFT, ROPE or RIGHT): the region to which the prior is
            assigned (default: ROPE)
        nsamples (int): the number of Monte Carlo samples
    
    Returns:
        2-d array with rows corresponding to samples and columns to
        probabilities `[p_left, p_rope, p_right]`
    """
    if x.ndim == 2:
        zm = x[:, 1] - x[:, 0]
    nm=len(zm)
    if prior_place==ROPE:
        z0=[0]
    if prior_place==LEFT:
        z0=[-float('inf')]
    if prior_place==RIGHT:
        z0=[float('inf')]
    z=np.concatenate((zm,z0))
    n=len(z)
    z=np.transpose(np.asmatrix(z))
    X=np.matlib.repmat(z,1,n)
    Y=np.matlib.repmat(-np.transpose(z)+2*rope,n,1)
    Aright = heaviside(X-Y)
    X=np.matlib.repmat(-z,1,n)
    Y=np.matlib.repmat(np.transpose(z)+2*rope,n,1)
    Aleft = heaviside(X-Y)
    alpha=np.concatenate((np.ones(nm),[prior_strength]),axis=0)
    samples=np.zeros((nsamples,3), dtype=float)
    for i in range(0,nsamples):
        data = np.random.dirichlet(alpha, 1)
        samples[i,2]=numpy.inner(np.dot(data,Aright),data)
        samples[i,0]=numpy.inner(np.dot(data,Aleft),data)
        samples[i,1]=1-samples[i,0]-samples[i,2]
     
    return samples

def signrank(x, rope, prior_strength=0.6, prior_place=ROPE, nsamples=50000,
             verbose=False, names=('C1', 'C2')):
    """
    Args:
        x (array): a vector of differences or a 2d array with pairs of scores.
        rope (float): the width of the rope 
        prior_strength (float): prior strength (default: 0.6)
        prior_place (LEFT, ROPE or RIGHT): the region to which the prior is
            assigned (default: ROPE)
        nsamples (int): the number of Monte Carlo samples
        verbose (bool): report the computed probabilities
        names (pair of str): the names of the two classifiers

    Returns:
        p_left, p_rope, p_right
    """
    samples = signrank_MC(x, rope, prior_strength, prior_place, nsamples)
    
    winners = np.argmax(samples, axis=1)
    pl, pe, pr = np.bincount(winners, minlength=3) / len(winners)
    if verbose:
        print('P({c1} > {c2}) = {pl}, P(rope) = {pe}, P({c2} > {c1}) = {pr}'.
              format(c1=names[0], c2=names[1], pl=pl, pe=pe, pr=pr))
    return pl, pe, pr


def plot_posterior(samples, names=('C1', 'C2')):
    """
    Args:
        x (array): a vector of differences or a 2d array with pairs of scores.
        names (pair of str): the names of the two classifiers

    Returns:
        matplotlib.pyplot.figure
    """
    return plot_simplex(samples, names)


def plot_simplex(points, names=('C1', 'C2')):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.pylab import rcParams

    def _project(points):
        from math import sqrt, sin, cos, pi
        p1, p2, p3 = points.T / sqrt(3)
        x = (p2 - p1) * cos(pi / 6) + 0.5
        y = p3 - (p1 + p2) * sin(pi / 6) + 1 / (2 * sqrt(3))
        return np.vstack((x, y)).T 

    vert0 = _project(np.array(
        [[0.3333, 0.3333, 0.3333], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]]))

    fig = plt.figure()
    fig.set_size_inches(8, 7)  
    
    nl, ne, nr = np.max(points, axis=0)
    for i, n in enumerate((nl, ne, nr)):
        if n < 0.001:
            print("p{} is too small, switching to 2d plot".format(names[::-1] + ["rope"]))
            coords = sorted(set(range(3)) - i)
            return plot2d(points[:, coords], labels[coords])

    # triangle
    fig.gca().add_line(
        Line2D([0, 0.5, 1.0, 0],
               [0, np.sqrt(3) / 2, 0, 0], color='orange'))
    # decision lines
    for i in (1, 2, 3):
        fig.gca().add_line(
            Line2D([vert0[0, 0], vert0[i, 0]],
                   [vert0[0, 1], vert0[i, 1]], color='orange'))
    # vertex labels
    rcParams.update({'font.size': 16})
    fig.gca().text(-0.08, -0.08, 'p({})'.format(names[0]))
    fig.gca().text(0.44, np.sqrt(3) / 2 + 0.05, 'p(rope)')
    fig.gca().text(1.00, -0.08, 'p({})'.format(names[1]))

    # project and draw points
    tripts = _project(points[:, [0, 2, 1]])
    plt.hexbin(tripts[:, 0], tripts[:, 1], mincnt=1, cmap=plt.cm.Blues_r)            
    # Leave some padding around the triangle for vertex labels
    fig.gca().set_xlim(-0.2, 1.2)
    fig.gca().set_ylim(-0.2, 1.2)
    fig.gca().axis('off')
    return fig
