# Demo script

[← Back to README](../README.md) · Pitch video: <https://youtu.be/1Gtmq5XUytc> · Live app:
<https://md8-habibullah.github.io/moon-material-simulator/>

A two-minute walkthrough for NASA Space Apps 2026, challenge **Abandoned but not Forgotten**. Every number below comes
from the app (checked against the browser engine on 13 November 2026).

1. **Start with the machines NASA left behind.** Click *Meet the machines*. On the Moon globe, open **Surveyor 3**:
   Apollo 12 brought its parts home after 31 months on the Moon, and NASA found that, apart from paint darkened by dust
   and sunlight, nothing had seriously failed. Switch to Mars and open **Ingenuity**: 72 flights, on a craft of 1.8 kg.
   Every machine out there is a materials experiment that never ended.
2. **Try it.** On Surveyor 3, press *Try it*. The simulator loads NASA Glenn's bacteria-grown bioplastic (Bio-PHB)
   with lunar mare dust and opens the part test for a wrench in the **lunar night** (−173 °C). Press *Load it until it
   breaks*.
3. **Design.** Set lunar highlands regolith to **10%**: tensile strength about 25 MPa and flexibility about 8%, strong
   with some give, which suits **tools**. Push to **50%**: stiffness rises to about 6.3 GPa and max service temperature
   to about 114 °C, but flexibility falls to about 3%, which suits **structures**. Open *Curves* to see the trend with
   **NASA's own measurements** plotted on top, and click any value to see the lab data behind it.
4. **Switch to Martian soil.** The grains turn rust-red and the decomposition temperature drops by about 11 °C, close
   to the 12–22 °C drop NASA Glenn measured for iron-rich Martian simulants.
5. **Optimize.** Choose *Wrench / hand tool*. The optimizer tests 4,662 mixes and recommends a fully local mix: 45%
   lunar highlands dust and 15% basalt fibre in Bio-PHB. Press **Load**. Then pick *Thruster nozzle*: it honestly reports
   that no plastic composite survives exhaust temperatures.
6. **Plan.** In *Impact*, 25 parts of 0.4 kg avoid 10 kg of launch mass, about $10M at NASA's upper delivery-cost
   figure.
7. **Close with the evidence.** In *Science*: on mixes the model never saw, the lab-data correction cuts the
   compressive-strength error from 230% (physics alone) to 34%, stiffness from 65% to 19% and density from 16% to 5%.
   A completely new study is harder (78%), and the app says so. Every value is traced to its page in NASA reports and
   peer-reviewed papers, and the code is open source.
