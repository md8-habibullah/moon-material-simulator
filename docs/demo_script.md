# Demo script

[← Back to README](../README.md) · Pitch video: <https://youtu.be/1Gtmq5XUytc> · Live app:
<https://md8-habibullah.github.io/moon-material-simulator/>

A 90-second walkthrough. Every number below comes from the app.

1. **Start with NASA's material.** The binder is Bio-PHB, the bacteria-grown plastic from NASA Glenn's 2026 work. Set
   lunar highlands regolith to **10%**. Tensile strength is about 27 MPa and flexibility about 8%: strong with some
   give, which suits **tools**. The donut shows 100% of the part can be made from local resources.
2. **Push to 50%.** Stiffness nearly doubles (about 7.6 GPa), density rises to about 1.7 g/cm³ and max service
   temperature climbs to about 115 °C: dense and heat-resistant, which suits **structures**. Open *Property curves* to
   see the trend and **NASA's own measurements** plotted on top.
3. **Switch to Martian soil.** The 3D grains and micrograph turn rust-red, and the accent colour follows. Decomposition
   temperature drops by about 14 °C, which is exactly what NASA Glenn measured for iron-rich Martian simulants.
4. **Optimize.** Choose *Wrench / hand tool*. The optimizer tests about 2,400 mixes and recommends a fully local PHB
   composite with regolith and basalt fibre. Press **Load**. Then pick *Thruster nozzle*: it honestly reports that no
   plastic composite survives exhaust temperatures, and points to sintered regolith instead.
5. **Compare and plan.** Save two formulas and open *Compare* to see the radar and winners per property. In *Impact*,
   25 parts of 0.4 kg avoid 10 kg of launch mass, or about $10M at NASA's upper launch-price figure.
6. **Close with the science.** In *Science*, the model scores R² ≥ 0.99 on held-out data, and its predictions sit 6%
   from NASA Glenn's PHB measurements on average. Everything is open source and built on NASA's Technical Reports
   Server.
