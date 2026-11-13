// "Abandoned but not Forgotten" (NASA Space Apps 2026): machines NASA left on the Moon and Mars, told for young explorers.
// Each one is a materials experiment that never ended, and each story ends with a hands-on test in the simulator.
// Facts are checked against the NASA source on each card (NSSDCA catalogue, NASA image library, NASA SP-284).
// Coordinates are approximate (about 0.1°). Longitude is east-positive; both maps put 0° at the centre.

const NSSDCA = (id) => `https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=${id}`;
const PHOTO = (id) => `https://images.nasa.gov/details/${id}`;

export const WORLDS = {
  // The Moon has no air, so only a faint rim; Mars gets a thin dusty-orange atmosphere.
  moon: { label: 'Moon', map: 'relics/moon-map.jpg', glow: 0x9fc4ff, glowStrength: 0.3 },
  mars: { label: 'Mars', map: 'relics/mars-map.jpg', glow: 0xff9a60, glowStrength: 0.55 },
};

export const RELICS = [
  {
    id: 'surveyor3',
    world: 'moon',
    name: 'Surveyor 3',
    kind: 'Robot lander',
    year: '1967',
    place: 'Ocean of Storms',
    lat: -3.01,
    lon: -23.42,
    images: [
      {
        src: 'relics/surveyor3.jpg',
        alt: 'An Apollo 12 astronaut stands next to the Surveyor 3 lander, with the Apollo 12 lunar module in the distance',
        credit: 'NASA, AS12-48-7134',
        link: PHOTO('AS12-48-7134'),
      },
    ],
    did: 'Landed in April 1967 and dug into the ground with a little scoop, to check that the Moon was firm enough for astronauts to land on. It was.',
    why: 'It was never built to come home. It stopped working when its first lunar night froze it.',
    science:
      'Two and a half years later, Apollo 12 landed about 160 m away. Pete Conrad and Alan Bean walked over and brought its camera, scoop and pieces of tubing back to Earth. About 40 teams of scientists studied them for more than a year: the first check of what the Moon does to a machine.',
    lesson:
      'The verdict, after 31 months on the Moon: apart from paint darkened by dust and sunlight, the materials had no serious failures. Machines can last there, if their materials can take the dust, the sun and the cold.',
    fact: "Apollo 12's own landing sandblasted Surveyor with flying dust. You can still see clean \"shadows\" where parts blocked the spray.",
    sources: [
      { label: 'NASA SP-284 (Apollo Lunar Surface Journal)', url: 'https://www.nasa.gov/history/alsj/UL12Sandblast.html' },
      { label: 'NASA NSSDCA: Surveyor 3', url: NSSDCA('1967-035A') },
    ],
    tryIt: { label: 'Make a Moon-dust tool and test it in the lunar night', part: 'wrench', env: 'night', regolith: 'lunar_mare' },
  },
  {
    id: 'apollo11-lrrr',
    world: 'moon',
    name: 'Apollo 11 laser reflector',
    kind: 'Science instrument',
    year: '1969',
    place: 'Sea of Tranquility',
    lat: 0.67,
    lon: 23.47,
    images: [
      {
        src: 'relics/apollo11-lrrr.jpg',
        alt: 'Buzz Aldrin on the Moon next to the instruments he just set up, with the lunar module Eagle behind him',
        credit: 'NASA, AS11-40-5948',
        link: PHOTO('as11-40-5948'),
      },
    ],
    did: 'Buzz Aldrin set it down in July 1969: a panel of 100 glass prisms that bounce light straight back to where it came from.',
    why: 'It needs no power, so it was always meant to stay, and scientists still use it more than 55 years later.',
    science:
      'Observatories on Earth still fire lasers at it and time the echo. That is how we know the Moon drifts about 3.8 cm farther from Earth every year.',
    lesson:
      'It sends back much less light than when it was new, most likely because Moon dust has settled on it. On the Moon, dust gets onto everything.',
    fact: 'The laser light makes a round trip of about 770,000 km in roughly 2.5 seconds.',
    sources: [{ label: 'NASA NSSDCA: Apollo 11 Lunar Module / EASEP', url: NSSDCA('1969-059C') }],
    tryIt: { label: 'Test a Moon-dust instrument mount in the lunar night', part: 'bracket', env: 'night', regolith: 'lunar_mare' },
  },
  {
    id: 'apollo15-rover',
    world: 'moon',
    name: 'Apollo 15 rover',
    kind: 'Moon car',
    year: '1971',
    place: 'Hadley Rille',
    lat: 26.13,
    lon: 3.63,
    images: [
      {
        src: 'relics/apollo15-rover.jpg',
        alt: 'Astronaut Jim Irwin working at the Lunar Roving Vehicle, with a mountain behind',
        credit: 'NASA, AS15-86-11603',
        link: PHOTO('as15-86-11603'),
      },
    ],
    did: 'The first car on the Moon. Dave Scott and Jim Irwin drove it about 28 km in three days, far more than they could have walked in spacesuits.',
    why: 'Only the small top half of the lander could fly back to orbit, so the rover was parked for good.',
    science: 'Driving let the crew reach the edge of a deep lunar valley and collect rocks from places no one could walk to.',
    lesson:
      'Its tyres had no rubber: rubber would crack in the sunlight and turn hard in the cold. Instead, engineers wove a mesh of zinc-coated piano wire with titanium treads. On the Moon, the material decides whether a part survives.',
    fact: 'Each rover was folded up like a book to fit on the side of the lander.',
    sources: [{ label: 'NASA NSSDCA: Apollo 15 Lunar Module', url: NSSDCA('1971-063C') }],
    tryIt: { label: 'Make a rover tool and test it in the noon heat', part: 'wrench', env: 'noon', regolith: 'lunar_highlands' },
  },
  {
    id: 'apollo17',
    world: 'moon',
    name: 'Apollo 17: the last camp',
    kind: 'Lander and rover',
    year: '1972',
    place: 'Taurus-Littrow valley',
    lat: 20.19,
    lon: 30.77,
    images: [
      {
        src: 'relics/apollo17-lro.jpg',
        alt: "Photo from lunar orbit: the Apollo 17 lander's bottom half still sits in the valley",
        credit: 'NASA/GSFC/Arizona State University, PIA12920',
        fit: 'contain',
        link: PHOTO('PIA12920'),
      },
      {
        src: 'relics/apollo17-fender.jpg',
        alt: 'Close-up of the Apollo 17 rover wheel with a replacement fender made from folded maps and clamps',
        credit: 'NASA, AS17-137-20979',
        link: PHOTO('as17-137-20979'),
      },
    ],
    did: 'December 1972, the last time people walked on the Moon. Gene Cernan and Harrison Schmitt explored the valley for three days.',
    why: 'The bottom half of their lander was the launch pad for the top half. It is still there, with a plaque: "Here man completed his first explorations of the Moon, December 1972 AD."',
    science: "In 2009 NASA's Lunar Reconnaissance Orbiter photographed the landing site from orbit. The lander is still visible, 37 years later.",
    lesson:
      'When a rover fender broke, the crew built a new one from four folded maps, tape and clamps. There are no spare-parts shops on the Moon: the nearest one is 384,000 km away.',
    fact: 'Fine dust spraying from a broken fender can coat suits and equipment, which is why the crew fixed it right away.',
    sources: [{ label: 'NASA NSSDCA: Apollo 17 Lunar Module', url: NSSDCA('1972-096C') }],
    tryIt: { label: 'Print a spare rover part from Moon dust', part: 'bracket', env: 'noon', regolith: 'lunar_mare' },
  },
  {
    id: 'viking1',
    world: 'mars',
    name: 'Viking 1 lander',
    kind: 'Robot lander',
    year: '1976',
    place: 'Chryse Planitia',
    lat: 22.27,
    lon: -47.95,
    images: [
      {
        src: 'relics/viking1.jpg',
        alt: "The first photo ever taken on the surface of Mars: rocks, dust and one of Viking 1's footpads",
        credit: 'NASA/JPL, PIA00381',
        position: 'right center',
        link: PHOTO('PIA00381'),
      },
    ],
    did: "Landed on 20 July 1976, NASA's first spacecraft to work on the surface of Mars. Its first photo, taken minutes after landing, shows its own footpad.",
    why: 'It worked for more than six years, until November 1982, when a wrong command pointed its antenna away from Earth.',
    science: 'It tested the soil for signs of life and recorded Mars weather day after day. The soil reacted in surprising ways that scientists still discuss.',
    lesson:
      "Mars dust is not Moon dust. NASA Glenn found that iron-rich Martian simulants lower the bioplastic's decomposition temperature by 12–22 °C, while lunar ones barely change it.",
    fact: "A footpad was the first thing photographed on Mars, so engineers could see how the soil held the lander's weight.",
    sources: [
      { label: 'NASA NSSDCA: Viking 1 Lander', url: NSSDCA('1975-075C') },
      { label: 'NASA Glenn, NTRS 20260007758', url: 'https://ntrs.nasa.gov/citations/20260007758' },
    ],
    tryIt: { label: 'Build a shelter brick from Mars dust', part: 'brick', env: 'habitat', regolith: 'martian' },
  },
  {
    id: 'sojourner',
    world: 'mars',
    name: 'Sojourner rover',
    kind: 'First Mars rover',
    year: '1997',
    place: 'Ares Vallis',
    lat: 19.13,
    lon: -33.22,
    images: [
      {
        src: 'relics/sojourner.jpg',
        alt: 'The small six-wheeled Sojourner rover among rocks on Mars',
        credit: 'NASA/JPL, PIA04318',
        link: PHOTO('PIA04318'),
      },
    ],
    did: 'Arrived with the Mars Pathfinder lander on 4 July 1997 and became the first wheeled rover on Mars. It weighed only 10.6 kg.',
    why: 'Built to last a week, it kept going for nearly three months, until the lander it talked through fell silent.',
    science: 'It drove up to rocks and measured what they are made of, the first time anyone did that on Mars.',
    lesson: 'Every kilogram flown to Mars costs a fortune, so Sojourner was as small as a microwave oven. Parts made on Mars from local dust would not need a rocket at all.',
    fact: 'The team gave the rocks it studied nicknames like "Barnacle Bill" and "Yogi".',
    sources: [{ label: 'NASA NSSDCA: Mars Pathfinder', url: NSSDCA('1996-068A') }],
    tryIt: { label: 'Make a rover tool from Mars dust', part: 'wrench', env: 'habitat', regolith: 'martian' },
  },
  {
    id: 'opportunity',
    world: 'mars',
    name: 'Opportunity rover',
    kind: 'Marathon rover',
    year: '2004',
    place: 'Meridiani Planum',
    lat: -2.0,
    lon: -5.5,
    images: [
      {
        src: 'relics/opportunity.jpg',
        alt: "Opportunity's robotic arm reaching out to a rock on the slope of a Martian valley",
        credit: 'NASA/JPL-Caltech, PIA20285',
        link: PHOTO('PIA20285'),
      },
    ],
    did: 'Planned to drive for 90 days, it explored for almost 15 years and drove 45 km: more than a marathon.',
    why: 'In June 2018 a dust storm covered the whole planet and its solar panels. NASA ended the mission in February 2019.',
    science: 'It found tiny round stones and minerals that form in water: strong evidence that liquid water once flowed where it drove.',
    lesson: 'Dust is the enemy of every machine on Mars and the Moon. Our idea flips that: use the dust itself as the building material.',
    fact: 'Scientists nicknamed the little round stones it found "blueberries".',
    sources: [{ label: 'NASA NSSDCA: Opportunity', url: NSSDCA('2003-032A') }],
    tryIt: { label: 'Test a Mars-dust bracket', part: 'bracket', env: 'habitat', regolith: 'martian' },
  },
  {
    id: 'ingenuity',
    world: 'mars',
    name: 'Ingenuity helicopter',
    kind: 'First Mars aircraft',
    year: '2021',
    place: 'Jezero crater',
    lat: 18.4,
    lon: 77.5,
    images: [
      {
        src: 'relics/ingenuity.jpg',
        alt: 'The tiny Ingenuity helicopter standing on the dusty floor of Jezero crater',
        credit: 'NASA/JPL-Caltech/ASU, PIA24648',
        link: PHOTO('PIA24648'),
      },
    ],
    did: 'On 19 April 2021 it made the first powered, controlled flight on another planet. It was planned to fly 5 times and flew 72.',
    why: 'In January 2024 a rotor blade was damaged during a landing, and it can no longer fly. It now stands still in the sand.',
    science: 'It scouted the way for the Perseverance rover and proved that aircraft can explore other worlds.',
    lesson: 'Mars air is about 1% as thick as Earth\'s, so Ingenuity weighs only 1.8 kg and its blades spin about 2,400 times a minute. Light, strong materials made it possible.',
    fact: 'It carries a small piece of fabric from the Wright brothers\' first airplane.',
    sources: [{ label: 'NASA NSSDCA: Mars 2020', url: NSSDCA('2020-052A') }],
    tryIt: { label: 'Make a light Mars-dust tool', part: 'wrench', env: 'habitat', regolith: 'martian' },
  },
];
