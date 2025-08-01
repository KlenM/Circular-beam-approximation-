import numpy as np
import scipy as sp
from pyatmosphere import gpu
from scipy.special import binom
import matplotlib.pyplot as plt
import circular_beam
from scipy.interpolate import make_interp_spline
from pyatmosphere import QuickChannel, measures
import analytics

gpu.config['use_gpu'] = True




plt.rcParams['axes.axisbelow'] = True
plt.rcParams["font.family"] = "DejaVu Serif"
plt.rcParams["font.serif"] = "STIX"
plt.rcParams["mathtext.fontset"] = "cm"
plt.rcParams.update({'font.size': 15})

save_kwargs = {
        "format": "pdf",
        "dpi": 300,
        "bbox_inches": "tight",
        "pad_inches": 0.005
        }



#----------------------------------

def get_Pn(eta, n, N, alpha_0, r, xi=0):
    eta = np.asarray(eta)

    def CNk(k):
        _numer = 2 * N * np.exp(-xi * (N - k) / N)
        _d1 = eta**2 * (N - k)**2
        _d2 = 2 * np.cosh(2 * r) * ((2 - eta) * N + eta * k) * eta * (N - k)
        _d3 = ((2 - eta) * N + eta * k)**2

        _sigma_inv_coef = eta * (N - k) / (_d1 + _d2 + _d3)
        _alpha_vec = np.asarray([np.conjugate(alpha_0), -alpha_0])
        _matrix = np.asarray([[
            eta * (N - k) * np.cosh(2 * r) + (2 - eta) * N + eta * k,
            -np.sinh(2 * r) * eta * (N - k)
        ], [
            -np.sinh(2 * r) * eta * (N - k),
            eta * (N - k) * np.cosh(2 * r) + (2 - eta) * N + eta * k
        ]])
        _expon = np.exp(_sigma_inv_coef * np.tensordot(
            np.tensordot(_alpha_vec, _matrix, axes=(0, 0)),
            np.conjugate(-_alpha_vec), axes=(0, 0)))
        return _numer / np.sqrt(_d1 + _d2 + _d3) * _expon
    adds = [binom(n, k) * (-1)**(n - k) * CNk(k) for k in range(n + 1)]
    return binom(N, n) * sum(adds)




def avrPn(pdts, t, n, N, alpha_0, r):
    sum=0
    count=0
    for i in t:
        sum=sum+get_Pn(i, n, N, alpha_0, r)*pdts[count]*(t[1]-t[0])
        count=count+1
    return sum


def get_avrPns(pdts, t, N, alpha_0, r, xi=0):
    return [avrPn(pdts, t,n,N,alpha_0,r) for n in range(N + 1)]


def avrEta(pdts, t):
    sum=0
    count=0
    for i in t:
        sum=sum+i*pdts[count]*(t[1]-t[0])
        count=count+1
    return sum

def avrEta2(pdts, t):
    sum=0
    count=0
    for i in t:
        sum=sum+i**2*pdts[count]*(t[1]-t[0])
        count=count+1
    return sum




def get_n_mean(alpha_0, r):
    return np.sinh(r)**2 + np.real(alpha_0)**2


def get_dn2_ord_mean(alpha_0, r):
    return np.sinh(r)**2 * np.cosh(2 * r) + np.real(alpha_0)**2 * (np.exp(-2 * r) - 1)


def get_Q(alpha_0, r):
    return get_dn2_ord_mean(alpha_0, r) / get_n_mean(alpha_0, r)


def Qout(alpha_0, r, eta_mean, eta2_mean, nu=0):
    Qin = get_Q(alpha_0, r)
    n_mean = get_n_mean(alpha_0, r)
    return eta2_mean * n_mean / (eta_mean * n_mean + nu) * Qin + (eta2_mean - eta_mean**2) * n_mean**2 / (eta_mean * n_mean + nu)


def mandel_array(Pn):
    N = np.asarray(Pn).shape[0]
    Pn = np.asarray([*Pn, 1 - np.sum(Pn)])
    k = np.arange(Pn.shape[0])
    c_mean = np.sum(k * Pn)
    c2_mean = np.sum(k**2 * Pn)
    dc2_mean = c2_mean - c_mean**2
    Q_B = N * dc2_mean / (c_mean * (N - c_mean)) - 1
    return Q_B
#----------------------------------

Mandel_circSim=[]
Mandel_circanaly=[]
Mandel_ancSim=[]
Mandel_ancanaly=[]
Mandel_sim=[]

Binom_circSim=[]
Binom_circanaly=[]
Binom_ancSim=[]
Binom_ancanaly=[]
Binom_sim=[]


frac=[]
longterm=0.02797
number_dot_app=20



for i in range(number_dot_app):
    aperture= 0.0085 + (1.3*longterm-0.0085) * i / number_dot_app
    l = 2000
    g = -15
    Cn2 = 10 ** g
    beam_w0 = (l * 8.08 * 10 ** (-7) / np.pi) ** 0.5

    quick_channel = QuickChannel(
        Cn2=Cn2,
        length=l,
        count_ps=6,
        beam_w0=beam_w0,
        beam_wvl=8.08e-07,
        aperture_radius=aperture,
        grid_resolution=512,
        F0=l,
        l0=1e-6,
        L0=5e3,
        f_min=1 / 5e3 / 15,
        f_max=1 / 1e-6 * 2

    )

    # -------------------

    sumx2_0 = 0
    sumW2 = 0
    sumW4 = 0

    etha = []

    sum_etha = 0
    sum_etha2 = 0

    n = 10 ** 5
    for i in range(n):
        output = quick_channel.run(pupil=False)

        W2 = 4 * (measures.mean_x2(quick_channel, output=output) -
                  (measures.mean_x(quick_channel, output=output)) ** 2)
        sumW2 = sumW2 + W2
        sumW4 = sumW4 + W2 ** 2

        sumx2_0 = sumx2_0 + (measures.mean_x(quick_channel, output=output)) ** 2

        # temp = temp + (measures.mean_x2(quick_channel, output=output)) ** 2
        temp_etha = measures.eta(quick_channel, output=quick_channel.run())
        etha.append(temp_etha)
        sum_etha = sum_etha + temp_etha
        sum_etha2 = sum_etha2 + temp_etha ** 2

    sim_W2 = sumW2 / n
    sim_W4 = sumW4 / n
    sim_x2_0 = sumx2_0 / n
    sim_etha = sum_etha / n
    sim_etha2 = sum_etha2 / n
    # ------------------------------

    analy_x2_0 = analytics.get_x2_0(quick_channel.source.k,quick_channel.source.w0,quick_channel.path.length ,quick_channel.get_rythov2())

    analy_W2 = analytics.get_W2(quick_channel.source.k,quick_channel.source.w0,quick_channel.path.length ,quick_channel.get_rythov2())

    analy_W4 = analytics.get_W4(quick_channel.source.k,quick_channel.source.w0,quick_channel.path.length ,quick_channel.get_rythov2())

    # --------------------------------------

    analy_etha = analytics.get_etha(quick_channel.source.k,quick_channel.source.w0,quick_channel.path.length ,quick_channel.get_rythov2(), quick_channel.pupil.radius)

    analy_etha2 = analytics.get_etha2(quick_channel.source.k,quick_channel.source.w0,quick_channel.path.length ,quick_channel.get_rythov2(), quick_channel.pupil.radius)

    #-----------------------------------------------------------
    determ_losses = 10 ** (-(3 + 0.1 * (quick_channel.path.length / 1000)) / 10)


    number_for_dots_pdt = 200

    # --------------------------------------------------------------

    t = np.linspace(0.00001, 1, num=number_for_dots_pdt)
    t_another = [x * determ_losses for x in t]

    etha = [x * determ_losses for x in etha]
    kde_sim = sp.stats.gaussian_kde(etha)
    pdt_etha=kde_sim.pdf(t)


    circ_sim = circular_beam.CircularBeamModel.from_beam_params(
        S_BW=np.sqrt(sim_x2_0),
        W2_mean=sim_W2,
        W4_mean=sim_W4,
        aperture_radius=quick_channel.pupil.radius
    )
    pdt_circ_sim = circ_sim.get_pdt(t)
    pdt_circ_sim_with_determ = [x / determ_losses for x in pdt_circ_sim]


    circ_analy = circular_beam.CircularBeamModel.from_beam_params(
        S_BW=np.sqrt(analy_x2_0),
        W2_mean=analy_W2,
        W4_mean=analy_W4,
        aperture_radius=quick_channel.pupil.radius
    )
    pdt_circ_analy = circ_analy.get_pdt(t)
    pdt_circ_analy_with_determ = [x / determ_losses for x in pdt_circ_analy]

    # ----------------------------------------------------------------

    acb_model_sim = circular_beam.AnchoredCircularBeamModel.from_beam_params(
        S_BW=np.sqrt(sim_x2_0),
        eta_mean=sim_etha,
        eta2_mean=sim_etha2,
        aperture_radius=quick_channel.pupil.radius,
        initial_guess_W2_mean=sim_W2,
        initial_guess_W4_mean=sim_W4
    )

    pdt_anc_sim = acb_model_sim.get_pdt(t)
    pdt_anc_sim_with_determ = [x / determ_losses for x in pdt_anc_sim]

    acb_model_analy = circular_beam.AnchoredCircularBeamModel.from_beam_params(
        S_BW=np.sqrt(analy_x2_0),
        eta_mean=analy_etha,
        eta2_mean=analy_etha2,
        aperture_radius=quick_channel.pupil.radius,
        initial_guess_W2_mean=analy_W2,
        initial_guess_W4_mean=analy_W4
    )

    pdt_anc_analy = acb_model_analy.get_pdt(t)
    pdt_anc_analy_determ = [x / determ_losses for x in pdt_anc_analy]


    r=0.4
    alpha0=6

    #Mandel_sim.append(Qout(alpha0,r,avrEta(pdt_etha,t),avrEta2(pdt_etha,t)))
    Mandel_sim.append(Qout(alpha0, r, sim_etha*determ_losses, sim_etha2*determ_losses**2))
    Mandel_circSim.append(Qout(alpha0,r,avrEta(pdt_circ_sim,t)*determ_losses,avrEta2(pdt_circ_sim,t)*determ_losses**2))
    Mandel_circanaly.append(Qout(alpha0, r, avrEta(pdt_circ_analy, t)*determ_losses, avrEta2(pdt_circ_analy, t)*determ_losses**2))
    Mandel_ancSim.append(Qout(alpha0, r, sim_etha*determ_losses, sim_etha2*determ_losses**2))
    Mandel_ancanaly.append(Qout(alpha0, r, analy_etha*determ_losses, analy_etha2*determ_losses**2))
    frac.append(quick_channel.pupil.radius / longterm)



    Binom_sim.append(mandel_array(get_avrPns(pdt_etha,t,7,alpha0,r)))
    Binom_circSim.append(mandel_array(get_avrPns(pdt_circ_sim_with_determ, t_another, 7, alpha0, r)))
    Binom_circanaly.append(mandel_array(get_avrPns(pdt_circ_analy_with_determ, t_another, 7, alpha0, r)))
    Binom_ancSim.append(mandel_array(get_avrPns(pdt_anc_sim_with_determ, t_another, 7, alpha0, r)))
    Binom_ancanaly.append(mandel_array(get_avrPns(pdt_anc_analy_determ, t_another, 7, alpha0, r)))



#-----------------------------------------------------------------
fig, ax = plt.subplots(1, 1)
X_ = np.linspace(np.min(frac), np.max(frac), 200)


X_Y0_Spline = sp.interpolate.make_interp_spline(frac, Mandel_sim)

Y0_ = X_Y0_Spline(X_)

plt.plot(X_,Y0_,linewidth='2',color='C0')



X_Y_Spline = sp.interpolate.make_interp_spline(frac, Mandel_circSim)

Y_ = X_Y_Spline(X_)

plt.plot(X_,Y_,linewidth='2',color='r')


X_Y1_Spline = sp.interpolate.make_interp_spline(frac, Mandel_circanaly)

Y1_ = X_Y1_Spline(X_)

plt.plot(X_,Y1_,linewidth='2',color='green')


X_Y2_Spline = sp.interpolate.make_interp_spline(frac, Mandel_ancSim)

Y2_ = X_Y2_Spline(X_)

plt.plot(X_,Y2_,color='orange',linewidth='2', linestyle='dashed')


X_Y3_Spline = sp.interpolate.make_interp_spline(frac, Mandel_ancanaly)

Y3_ = X_Y3_Spline(X_)

plt.plot(X_,Y3_,color='violet',linewidth='2', linestyle='dashed')






ax.grid()
ax.set_ylim(-0.3, 0.2)
ax.set(xlabel=r'Normalized aperture radius $a/W_{\text{LT}}$', ylabel='Mandel $Q$ parameter')
plt.savefig("app_Mandel.pdf", **save_kwargs)

#------------------------------------------------------------------------------


fig, ax = plt.subplots(1, 1)
X_ = np.linspace(np.min(frac), np.max(frac), 200)


X_Y0_Spline = sp.interpolate.make_interp_spline(frac, Binom_sim)

Y0_ = X_Y0_Spline(X_)

plt.plot(X_,Y0_,linewidth='2',color='C0')



X_Y_Spline = sp.interpolate.make_interp_spline(frac, Binom_circSim)

Y_ = X_Y_Spline(X_)

plt.plot(X_,Y_,linewidth='2',color='r')


X_Y1_Spline = sp.interpolate.make_interp_spline(frac, Binom_circanaly)

Y1_ = X_Y1_Spline(X_)

plt.plot(X_,Y1_,linewidth='2',color='green')


X_Y2_Spline = sp.interpolate.make_interp_spline(frac, Binom_ancSim)

Y2_ = X_Y2_Spline(X_)

plt.plot(X_,Y2_,color='orange',linewidth='2', linestyle='dashed')


X_Y3_Spline = sp.interpolate.make_interp_spline(frac, Binom_ancanaly)

Y3_ = X_Y3_Spline(X_)

plt.plot(X_,Y3_,color='violet',linewidth='2', linestyle='dashed')






ax.grid()
ax.set_ylim(-0.7, 0.1)
ax.set(xlabel=r'Normalized aperture radius $a/W_{\text{LT}}$', ylabel='Binomial $Q_{7}$ parameter')
plt.savefig("app_Binomial.pdf", **save_kwargs)

