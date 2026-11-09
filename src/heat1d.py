"""1D vertical heat diffusion in a column of ice.

Depth z points downwards, from the upper boundary (z = 0, a depth below the surface where the seasonal
cycle is damped, ~10–20 m) to the bed (z = H). Heat transfer by conduction only (no advection, no
meltwater, no lateral flow): hanging glaciers are thin and move slowly, but the borehole data show
that refreezing meltwater near the surface matters (see notebook 06).

    rho c dT/dt = k d²T/dz²
    upper boundary: T(0, t) = T_top(t)
    bed:            k dT/dz = G (geothermal heat flux, heat entering from below)
    everywhere:     T <= T_pmp(depth) (pressure melting point; surplus heat is assumed to melt ice)

Values from Cuffey & Paterson (2010), The Physics of Glaciers, 4th ed. [verify].
"""

import numpy as np

K = 2.1                  # thermal conductivity of ice (W m-1 K-1)
RHO = 917.0              # density of ice (kg m-3)
C = 2050.0               # specific heat of ice near 0 °C (J kg-1 K-1)
KAPPA = K / (RHO * C)    # thermal diffusivity (m2 s-1)
G = 0.07                 # geothermal heat flux (W m-2), typical continental value [verify for the Alps]
BETA = 8.7e-4            # lowering of the melting point with depth (K m-1), air-saturated ice [verify]
YEAR = 365.25 * 86400.0


def melting_point(depth):
    """Pressure melting point (°C) at a depth below the ice surface (m)."""
    return -BETA * np.asarray(depth, float)


def steady_profile(t_top, z_top, z, g=G):
    """Steady-state temperature at depths z (m below the surface), with T = t_top at depth z_top.

    Conduction only, so the profile is linear: the gradient G/K (≈ 0.03 K per m) is set by the geothermal flux.
    """
    t = t_top + g / K * (np.asarray(z, float) - z_top)
    return np.minimum(t, melting_point(z))


def basal_temperature(t_top, z_top, thickness, g=G):
    """Steady-state temperature at the bed (°C)."""
    return steady_profile(t_top, z_top, thickness, g)


def response_time(thickness):
    """Characteristic time (years) for a change of the upper boundary temperature to reach the bed: H² / kappa."""
    return np.asarray(thickness, float) ** 2 / KAPPA / YEAR


def transient(t_initial, z, t_top, years, dt_days=10, g=G):
    """Implicit finite-difference solution.

    z: depths below the ice surface (uniform grid, z[0] = upper boundary, z[-1] = bed)
    t_initial: initial temperature at depths z
    t_top: function of time (years since the start) giving the upper boundary temperature
    years: duration. Returns (times in years, temperatures with shape (len(times), len(z))).
    """
    z = np.asarray(z, float)
    dz = z[1] - z[0]
    dt = dt_days * 86400.0
    n = len(z)
    r = KAPPA * dt / dz**2
    # matrix of the implicit scheme: -r T[i-1] + (1 + 2r) T[i] - r T[i+1] = T_old[i]
    a = np.zeros((n, n))
    a[0, 0] = 1.0                                   # Dirichlet at the top
    for i in range(1, n - 1):
        a[i, i - 1:i + 2] = [-r, 1 + 2 * r, -r]
    a[-1, -2:] = [-2 * r, 1 + 2 * r]                # Neumann at the bed (ghost node), flux added below
    a_inv = np.linalg.inv(a)
    t_pmp = melting_point(z)

    steps = int(round(years * YEAR / dt))
    times = np.arange(steps + 1) * dt / YEAR
    out = np.empty((steps + 1, n))
    temp = np.minimum(np.asarray(t_initial, float), t_pmp)
    out[0] = temp
    for s in range(1, steps + 1):
        rhs = temp.copy()
        rhs[0] = t_top(times[s])
        rhs[-1] += 2 * r * dz * g / K
        temp = np.minimum(a_inv @ rhs, t_pmp)
        out[s] = temp
    return times, out
