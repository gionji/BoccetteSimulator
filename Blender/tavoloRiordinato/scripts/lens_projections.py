import numpy as np

def rectilinear(f, theta): 
    return f * np.tan(theta)

def fisheye_stereographic(f, theta):
    return 2.0 * f * np.tan(theta / 2)

def fisheye_equidistant(f, theta):
    return f * theta

def fisheye_equisolid(f, theta):
    return 2.0 * f * np.sin(theta / 2)

def fisheye_orthogonal(f, theta):
    return f * np.sin(theta)