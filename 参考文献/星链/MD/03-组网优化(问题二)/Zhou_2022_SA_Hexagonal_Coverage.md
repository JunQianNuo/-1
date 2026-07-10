---
raw_title: Optimized Design Method for Satellite Constellation Configuration Based on Real-time Coverage Area Evaluation
subject: 星链数模-参考文献
problem: 问题二·组网优化
source: 2209.09131v2.pdf
status: pdftotext提取（公式/图表排版散乱，待校对）
parser: pdftotext
topics:
  - 模拟退火
  - 六边形离散
  - 实时覆盖评价
  - Walker星座
---

> [!warning] 提取说明
> 本文件为 `2209.09131v2.pdf` 的 **pdftotext 原文提取**（MinerU 本地在本机 502 失败，见文档转MD规范降级链）。公式与图表排版散乱、图片缺失；**干净公式、模型与算法解读见** [[数学建模/第一次/参考文献/星链/中文精读/03-组网优化(问题二)/Zhou_2022_SA_Hexagonal_Coverage|中文精读]]。

---

Optimized Design Method for Satellite Constellation Configuration Based on Real-time
Coverage Area Evaluation
Jiahao Zhou1, Boheng Li2, Qingxiang Meng1* 1School of Remote Sensing and Information Engineering, Wuhan University, Wuhan, China
2School of Cyber Science and Engineering, Wuhan University, Wuhan, China *Corresponding author, e-mail: mqx@whu.edu.cn

arXiv:2209.09131v2 [cs.CV] 6 Dec 2022

Abstract--When using constellation synergy to image large areas for reconnaissance, it is required to achieve the coverage capability requirements with minimal consumption of observation resources to obtain the most optimal constellation observation scheme. With the minimum number of satellites and meeting the real-time ground coverage requirements as the optimization objectives, this paper proposes an optimized design of satellite constellation configuration for full coverage of largescale regional imaging by using an improved simulated annealing algorithm combined with the real-time coverage evaluation method of hexagonal discretization. The algorithm can adapt to experimental conditions, has good efficiency, and can meet industrial accuracy requirements. The effectiveness and adaptability of the algorithm are tested in simulation applications.
Keywords--Constellation design;Track of subsatellite point;simulated annealing; hexagonal discretization
I. INTRODUCTION
Satellite ground-imaging coverage technology is widely used [1], and research on this technology continuously intensifies. In constellation optimization design, scenarios are often encountered in which multiple imaging satellites need to be used to collaborate in imaging observations of a larger regional target. To ensure satellite coverage of a specific target or region while reducing the cost required to complete the mission, it is essential to design a reasonable constellation distribution of satellites for ground imaging coverage.
Consider the following satellite usage scenario: within a short time zone, the user department urgently needs image data for a certain larger area, but due to the short time given and the small number of coverage opportunities, the area cannot be captured in its entirety even if all coverage opportunities are used [2]. In this case, to maximize the coverage efficiency as much as possible, it is desired to develop a constellation-optimized design solution that achieves the required average coverage of the target area with the least consumption of resources. The problem is optimizing satellite constellation configuration based on coverage area evaluation in the resource-limited scenario.
In this paper, we develop a novel solution model based on the hexagonal discretization technique and simulated annealing

algorithm, and propose a new solution strategy to optimize the constellation configuration that meets the maximum observation area requirement, and output a variety of different satellite constellation configurations for selection. Simulation experiments show that the proposed strategy can obtain highquality solutions in an acceptable time.
II. SATELLITE ORBIT COVERAGE MODEL A. Calculation of subsatellite point track
During the operation of remote sensing satellites, the subsatellite tracks of their adjacent orbital periods cannot be completely coincident due to the influence of the Earth's rotation and ingress, which is one of the most basic bases for designing the return orbit. Therefore, to calculate the subsatellite track during the operation of the satellite, the results of the subsatellite track in a single orbital period need to be calculated first.
The track of the subsatellite point is usually expressed by the right ascension  and declination . When only the effect of Earth's rotation is considered[3], we can obtain the right ascension and declination of the satellite's hypostasis directly according to the six roots of the satellite's orbit shown in Table 1, and the position parameters of the satellite's hypostasis on Earth are shown in Fig. 1.
Fig. 1. Illustration of the parameters of the subsatellite point position

TABLE I SIGNIFICANCE OF THE NUMBER OF ORBITAL ELEMENTS

Symbol a e i   M

Descripton semi major axis
eccentricity inclination longitude of ascending node argument of periapsis true anomal

For the calculation of multiple orbital periods,the influence

of the Earth's uptake also needs to be considered. In this

paper, we adopt the J2 uptake model commonly used to fit

Fig. 2. Calculated track of the subsatellite point

satellite orbits, at which time, let E be the angular velocity

of the Earth's rotation, the satellite's subsatellite point track is

calculated as

For all types of sensors, their coverage boundaries can be

considered as the intersection of their sensor boundary point

d

observation vectors with the ground, as shown in Figure 3.

 = 0+arctan(cos(i) - tan( + f )) - SG0 - E - dt (t - t0)

(1)

 = arcsin(sin(i) - sin( + f ))

(2)

For the average root, a, e, and i do not change and , , and M change with time.

d dt

=

-

3nJ2Re2 2a2 (1 - e2

)2

cos(i)

(3)

d dt

=

-

3nJ2Re2 2a2 (1 - e2

)2

5 sin2(i) - 2 2

(4)

dM =n-

3nJ2

Re 2 3 sin2(i) - 1

(5)

dt

2 (1 - e2)3 a

2

The track of the subsatellite points of adjacent orbital periods are the same, and their longitude differences are

d

2 = - E - dt T

(6)

Here, J2 is the uptake coefficient, while n is the velocity of the earth's rotation in translational motion

Therefore, if the six orbital roots at the moment t0 and the Greenwich sidereal time SG(t0) are known, we can perform the simulation calculation of the subsatellite point track. The subsatellite point track calculated according to equation (1)(2)(3)(4)(5)(6) is shown in Fig. 2.

B. Satellite ground coverage calculation
The coverage calculation is achieved by establishing the initial observation vector based on the geometry and parameters of the sensor field of view. At the same time, calculating the mapped positions on the Earth's surface corresponding to the sensor boundary units is based on the ephemeris parameters of the satellite, attitude parameters, and the Earth ellipsoidal model [4].

Fig. 3. Schematic diagram of satellite imaging coverage area

The sensor surface center is the origin O, the Z-axis points

to the center of the earth, the X-axis is the satellite flight

direction, the Y-axis is perpendicular to the flight direction,

point N is any point on the sensor circle boundary, point

M is a point on the boundary and on the Y-axis, then the

observation vector F N at any point on the garden boundary

can be obtained by turning F M along the Z-axis by an angle

aonf d.l Nioste[x,thya,tz]Tl

.

is the observation vector Let |OF | = f , the conic

of the section

sensor circle

radius

|OM |

=

r,

then

T

M = [0, r, 0] ,

F

=

[0, 0, -f ]T ,

FM

=

[0, r, f ]T ,

and

the

specific

definition

is

shown

below.

  cos sin 0

 rsin 

l = -sin cos 0 FM = rcos

(7)

0

01

f

Let

r f

=

tan,

and

then

normalize

to

obtain

x = tan  sin

y = tan  cos

(8)

 z=1

Where  is the half-field-of-view angle and  is the middle

angle

in

the

half-field-of-view

range

of

the

sensor.

=

2 n

,

and

when n is 2, it is a line-array push-and-sweep sensor. When n is 4, it is a frame-amplitude sensor.

 

L

=

arctan

Y X

 B
   

=

arctan

 X

Z 2 +Y

2

H=

X 2 +Y cosB

2

1+

ae2 Z

-

 sinB
1-e2 sin2 B

- a
1-e2 sin2 B

(9)

Equation (9) is used to convert the spatial Cartesian coordinates into latitude, longitude, and elevation in the geodetic coordinate system. The resulting computed coverage simulation model of the frame-width sensor satellite is shown in Figure 4.

IV. REAL-TIME COVERAGE EVALUATION METHOD WITH
HEXAGONAL DISCRETIZATION
In order to quickly calculate the coverage of the target area by multiple satellites in a given time range [5], this paper proposes a new algorithm based on a dissected hexagonal grid:
1) Discretize the hexagon of the target area 2) Determine the intersection of each grid with the satellite
coverage zone 3) Divide the number of intersecting grids by the number
of all grids as the coverage at the current moment 4) Obtain the average coverage by counting the coverage
at different time periods

Fig. 4. Simulation calculation of satellite ground coverage

III. SATELLITE STATE SPACE MODEL
The Walker constellation configuration has good global and latitudinal band coverage characteristics and is widely used. All the satellite orbits in this constellation are nearly circular with equal semi-long axis, eccentricity, and orbital inclination, and the satellites are evenly distributed in the same orbital plane.
The configuration code of a Walker constellation is N/P/F (number of satellites/number of orbital planes/phase factor). The longitude of ascending node and the argument of latitude of any satellite numbered m in the constellation are.

Fig. 5. Coverage analysis method based on hexagonal grid

As shown in Figure 5, there are 26 hexagonal grids in

the target area, and the satellite coverage bands are abcd and

ABCD. The grids intersecting with abcd are 1, 2, 5, 8, 11,

15, 18, 21, 24, 25, and the grids intersecting with ABCD are

9, 13, 16, 19, 22, 25. 15 grids are covered, and the coverage

rate

is

15 26

= 54.2%.

360

m = P (Pm - 1)

(10)

360

360

um = S (Nm - 1) + N F (Pm - 1)

(11)

Where S is the number of satellites in each orbital plane,

Pm is the number of the orbital plane in which the satellite is

located, and Nm is the number of the satellite in the orbital

plane.

That

is,

S

=

N P

,Pm

=

m S

- 1,

Nm

=

m

- (Pm

- 1) S

To meet the coverage requirement of the target area with

good global coverage performance, we choose the Walker

constellation configuration as the experimental configuration in

this paper to search for the optimal solution in this state space.

The solutions for other constellations can also be calculated

using the algorithm proposed below.

Fig. 6. Coverage analysis method based on hexagonal grid
As shown in Figure 6, the hexagonal grid method is closer to the actual covered area in the coverage analysis of circular areas than the meridional grid method. It has better performance in dealing with irregular areas.
V. CONSTELLATION CONFIGURATION OVERLAY
OPTIMIZATION DESIGN ALGORITHM
The simulated annealing algorithm is derived from the solid annealing principle. This probability-based algorithm heats the solid to a sufficiently high temperature and then lets it cool down slowly.

To ensure the uniformity of revisit time and meet the revisit time demand in different latitudes, a multi-inclination orbit combination scheme is used here, in which multiple satellites with the same inclination angle adopt the W alker- distribution [6]. For larger area targets with larger state space, the idea of a simulated annealing algorithm is considered to accelerate the search speed. When a satellite constellation configuration satisfying the revisit time requirement is not found, the algorithm will search it in a certain way in the range where the number of satellites increases; when a satellite constellation configuration satisfying the revisit time is found, the algorithm will search it in the range where the number of satellites is less than that satellite constellation configuration. The specific steps are as follows.

1) Given a higher initial temperature T = T0, enter an initial solution
2) Determine whether the target region in this state satisfies the coverage constraint, if yes, go to step 3; otherwise, go to step 6
3) Store the solution as the better solution, and if the solution is the current solution with the least number of satellites used, then it will be the current optimal solution, otherwise with probability exp [-100/ [n  T ]] the solution is the current optimal solution, where n is the number of iterations
4) Change the orbital inclination angle within a certain range according to the current optimal solution and coverage area, which decreases with temperature, and take the case of maximum average coverage
5) Subtract 1 from the number of orbital planes or the number of satellites in the plane corresponding to each inclination angle of the current optimal solution with a probability of 50%T . If the annealing is finished, go to step 7, otherwise go to step 2
6) Add 1 to the number of orbital planes or the number of satellites in the plane corresponding to each inclination angle of the current optimal solution with a probability of 50%T . If the annealing is finished, go to step 7, otherwise go to step 2
7) Output the current optimal solution as the optimal constellation configuration

Fig. 7. Coverage analysis method based on hexagonal grid

TABLE II SATELLITE EXPERIMENT PARAMETERS

Parameters orbital radius eccentricity true anomal effective field of view satellite sensor type
Target coverage area boundary points

Value 8576km
0.0 0.0- 60- frame width sensors [100.382447- N, 19.47806- E] [100.382447- N, 43.47806- E] [124.382447- N, 43.47806- E] [124.382447- N, 19.47806- E]

The algorithm steps are shown in Figure 7.
VI. SIMULATION EXPERIMENTS
Experiments are conducted according to the satellite parameters described in Table 2. The experimental environment was Python 3.7 with 16G of computing memory, and the coverage calculation was hosted using ArcGIS API for Python to improve computing efficiency. The initial constellation is set to i = 40 W alker 6/3/1, and the parameters of the simulated annealing algorithm are selected as T = 1, Tmin = 0.01,  = 0.98. The average coverage is defined as the average of the instantaneous coverage of any of the 50 selected moments during 30 satellite operation periods [7]. The minimum number of satellites is required to search the

constellation for the region's average coverage of 70%. The optimal solution is obtained when the number of satellites is 54, the average coverage is 72.7%, and the configuration of the satellite constellation is i = 38 W alker 54/9/1, where the Walker constellation configuration code is N/P/F (number of satellites/number of orbital planes/phase factor).
Figure 8 shows the instantaneous coverage of this optimized constellation for 100 moments. We can see that the constellation has a relatively uniform coverage of the target area with good performance[8].
Figures 9 and 10 show the changes in obtaining the optimal solution and the changes in the average coverage of the

constellation during the search. We can see that the improved simulated annealing algorithm can search for the optimal solution at the 26th iteration, which is faster, and the average coverage of the generated constellation is stable around the target range with the increase in the number of iterations, which has a good performance.

Fig. 8. Variation of the instantaneous coverage of the best-configuration constellation during the operational cycle

VII. CONCLUSION
This paper proposes a constellation design and optimization method based on hexagonal discretization and a simulated annealing algorithm for large-scale imaging regions. Compared with traditional design methods, this method can reduce the number of satellites to be launched to complete the constellation construction task, thus reducing the time and cost required to complete the full satellite deployment. The reduction in the number of satellites also reduces the simultaneous co-location coverage area, thus reducing the amount of data to be processed and the processing time. The designed algorithm is scalable and scalable and can be modified to output multiple constellation configurations that meet the revisit time requirements. The solution can design and select constellation configurations faster, which is of great significance for area-specific surveillance, disaster monitoring, and military reconnaissance.

VIII. ACKNOWLEDGMENT
The authors would like to thank the anonymous reviewers for their valuable feedback and suggestions. The authors would also like to express their gratitude to their colleagues and mentors who provided support and guidance throughout Jiahao's writing process. Boheng and Jiahao made equal technical contribution for this work.

Fig. 9. Variation of the number of optimal solution satellites with the number of iterations

REFERENCES
[1] Ulybyshev. Y, "Satellite constellation design for complex coverage," Journal of Spacecraft and Rockets, vol.45(4), 2008, pp.843-849.
[2] Ferringer. MP, Spencer DB, "Satellite constellation design tradeoffs using multiple-objective evolutionary computation," Journal of spacecraft and rockets, vol.43(6), 2006, pp.1404-1411.
[3] Zhang. YB, Zhang. YS, "Calculation of Subsatellite point Trajectories for Near-circular Orbit Remote Sensing Satellites," Journal of Institute of Surveying and Mapping, vol.04, 2001, pp.257-259.
[4] Seyedi. Y, Safavi. SM, "On the analysis of random coverage time in mobile LEO satellite communications," IEEE Communications Letters, vol.16(5), 2012, pp.612-615.
[5] Li. Y, Zhao. S, Wu. J, "A general evaluation criterion for the coverage performance of LEO constellations," Aerospace Science and Technology, vol.48, 2016, pp.94-101.
[6] Yu. YJ, Wang. F, Miao Y, "Optimal Design of Constellation Configuration for Irregular Imaging Area Coverage Based on Improved Simulated Annealing Algorithm," Chinese Journal of Space Science, vol.39(04), 2019, pp.494-501.
[7] Whittecar. WR, Ferringer. MP, "Global coverage constellation design exploration using evolutionary algorithms. In AIAA/AAS Astrodynamics Specialist Conference," 2014, pp.4159.
[8] Ulybyshev. Y, "Geometric analysis of low-earth-orbit satellite communication systems: covering functions," Journal of Spacecraft and Rockets, vol.37(3), 2000, pp.385-391.

Fig. 10. Variation of average coverage of constellations with the number of iterations during the search

