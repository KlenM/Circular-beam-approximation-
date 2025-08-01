import numpy as np
from pyatmosphere import gpu
import matplotlib.pyplot as plt
import scipy as sp
from pyatmosphere import QuickChannel, measures


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





z_ax=[]
x_ax=[]
number_dot=10
for i in range(number_dot):

    l = 500+(5500-500)*i/number_dot
    g = -15
    Cn2 = 10 ** g
    beam_w0 = (l * 8.08 * 10 ** (-7) / np.pi) ** 0.5

    quick_channel = QuickChannel(
        Cn2=Cn2,
        length=l,
        count_ps=6,
        beam_w0=beam_w0,
        beam_wvl=8.08e-07,
        aperture_radius=0.011,
        grid_resolution=512,
        F0=l,
        l0=1e-6,
        L0=5e3,
        f_min=1 / 5e3 / 15,
        f_max=1 / 1e-6 * 2

    )


    # -------------------

    dataW2 = []
    datax2_0=[]
    sumx2_0=0
    sumW2 = 0
    sumW4 = 0
    n = 10 ** 5
    for i in range(n):
        output = quick_channel.run(pupil=False)

        W2 = 4 * (measures.mean_x2(quick_channel, output=output) -
                  (measures.mean_x(quick_channel, output=output)) ** 2)
        x2_0=measures.mean_x(quick_channel, output=output)**2

        sumx2_0=sumx2_0+ x2_0
        datax2_0.append(x2_0)
        sumW2 = sumW2 + W2
        sumW4 = sumW4 + W2 ** 2
        dataW2.append(W2)

    # ------------
    meanx2_0= sumx2_0/n
    meanW2 = sumW2 / n
    meanW4 = sumW4 / n

    mu = np.log((meanW2 ** 2) / (meanW4 ** 0.5))
    sigma2 = np.log(meanW4 / (meanW2 ** 2))

    #print('mean for lognormal', mu)
    #print('variance for lognormal', sigma2)

    # -------------------


    x_ax.append(quick_channel.get_rythov2())

    z_ax.append(np.corrcoef(dataW2, datax2_0)[0,1])


#---------------------

X_Z_Spline = sp.interpolate.make_interp_spline(x_ax, z_ax)

X_ = np.linspace(np.min(x_ax), np.max(x_ax), 200)
Z_ = X_Z_Spline(X_)



fig2, ax2 = plt.subplots(1, 1)
plt.plot(X_,Z_,linewidth='2')
plt.plot(x_ax,z_ax,'go')
ax2.set(xlabel=r'Rytov parameter $σ^2_R$', ylabel=r'Correlation coefficient $ρ(S, x^2_0)$')

ax2.grid()


plt.savefig("corr_S_x2_0.pdf", **save_kwargs)

plt.show()
