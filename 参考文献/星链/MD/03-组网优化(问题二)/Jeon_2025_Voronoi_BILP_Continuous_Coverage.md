---
raw_title: Communication Constellation Design of Minimum Number of Satellites with Continuous Coverage and Inter-Satellite Link
subject: 星链数模-参考文献
problem: 问题二·组网优化
source: 2410.03354v3.pdf
status: pdftotext提取（公式/图表排版散乱，待校对）
parser: pdftotext
topics:
  - 有界Voronoi图
  - 共地面轨迹星座
  - BILP整数规划
  - APC分解
  - 连续覆盖
---

> [!warning] 提取说明
> 本文件为 `2410.03354v3.pdf` 的 **pdftotext 原文提取**（MinerU 本地在本机 502 失败，见文档转MD规范降级链）。公式与图表排版散乱、图片缺失；**干净公式、模型与算法解读见** [[数学建模/第一次/参考文献/星链/中文精读/03-组网优化(问题二)/Jeon_2025_Voronoi_BILP_Continuous_Coverage|中文精读]]。

---

arXiv:2410.03354v3 [physics.space-ph] 16 Mar 2025

AAS 25-254
COMMUNICATION CONSTELLATION DESIGN OF MINIMUM NUMBER OF SATELLITES WITH CONTINUOUS COVERAGE AND INTER-SATELLITE LINK
Soobin Jeon*, Sang-Young Park
The recent advancement in research on distributed space systems that operate a large number of satellites as a single system urges the need for the investigation of satellite constellations. Communication constellations can be used to construct global or regional communication networks using inter-satellite and ground-tosatellite links. This study examines two challenges of communication constellations: continuous coverage and inter-satellite link connectivity. The bounded Voronoi diagram and APC decomposition are presented as continuous coverage analysis methods. For continuity analysis of the inter-satellite link, the relative motion between adjacent orbital planes is used to derive analytic solutions. The Walker-Delta constellation and common ground-track constellation design methods are introduced as examples to verify the analysis methods. The common ground-track constellations are classified into quasi-symmetric and optimal constellations. The optimal common ground-track constellation is optimized using the BILP algorithm. The simulation results compare the performance of the communication constellations according to various design methods.
INTRODUCTION
In recent years, the feasibility of low Earth orbit communication satellites has attracted attention owing to the trend of small satellites. Examples include Space-X's Starlink, Eutelsat's OneWeb, and Amazon's Kuiper projects.1 Their orbits are designed to provide communication links across the Earth. A satellite constellation operates several satellites with distinct orbits in a single system. Compared with conventional geostationary satellites, low Earth orbit satellites have a smaller coverage size and shorter orbital periods, resulting in degraded spatial and temporal coverage performance. Therefore, low Earth orbit constellations operate several satellites to overcome this limitation while minimizing the number of satellites. If the coverage is continuous in the area of interest, the communication constellation can continuously provide communication links. In addition, when the inter-satellite links are connected, the link is not disconnected even by the orbital motion of the satellite and the Earth's rotation effect. In this study, the low Earth orbit communication constellation design problem was interpreted as the problem of achieving continuous coverage and inter-satellite links.
The sections are presented in the following order: constellation design methods, coverage analysis methods, relative motion in adjacent orbital planes, simulation results, and conclusions. Constellation design methods describe the basis of Walker and common ground-track constellations.
*PhD Candidate, Department of Astronomy, Yonsei University, 50 Yonsei-ro, Seodaemun-gu, 614A Science building, Seoul, Korea. Professor, Department of Astronomy, Yonsei University, 50 Yonsei-ro, Seodaemun-gu, 624 Science building, Seoul, Korea.
1

The Walker constellation first introduces the concept of a seed satellite and its design parameters, and defines the orbital elements. The pattern repetition period and duplicate allocation of orbital elements are explained as two important characteristics of the Walker-Delta constellation, and are expressed by the design parameters. The repeat ground-track orbit is the seed satellite orbit for a common ground-track constellation. The quasi-symmetric method configures satellites such that the spacing between adjacent satellites is almost equal. The BILP method optimizes the satellite configuration to satisfy the coverage requirements while minimizing the total number of satellites. The coverage analysis methods section first explains a useful concept: the geometry of the Earth's coverage. Then, Voronoi tessellation and APC decomposition are described with the references. The relative motion in adjacent orbital planes derives the key formulae to analyze the bounds of the relative distance. The simulation results present the continuous coverage analyses for the WalkerDelta, quasi-symmetric, and BILP constellations, and the inter-satellite link continuity analyses for the three constellations. The last section summarizes and concludes the contents of this paper. CONSTELLATION DESIGN METHODS Walker Constellation
The Walker constellation is a geometric design method that symmetrically configures the orbits.2,3 The seed satellite determines the common orbital elements of the constellation. For the Walker constellation, the satellites are configured in circular orbits with the same semi-major axis (a), inclination (i), and argument of perigee () of the seed satellites. The two types of Walker constellations are classified according to their inclinations. The Walker-Star constellation is designed based on a polar orbit and achieves global coverage. On the other hand, the Walker-Delta constellation has an inclination under 90 degrees and covers the mid-latitude and equator regions. Therefore, this classification is relevant only to the latitude of the area of interest (AoI).
The three design parameters are the total number of satellites (T ), number of orbital planes (P), and phasing parameter (F  {0, 1, ..., P - 1}). The number of satellites per orbital plane (S = T/P) is an auxiliary parameter used to prevent confusion. The right ascension of ascending node (RAAN, m) and mean anomaly (Mm,n) of the nth satellite in the mth orbital plane (S ATm,n) are defined by
Figure 1. Geometric description of the orbital elements of the Walker-Delta constellation
2

Eqs. (1) and (2), as shown in Figure 1.

m

=

360 P

-

(m

-

1) deg

(1)

Mm,n

=

360 T

-

F

-

(m

-

1)

+

360 S

-

(n

-

1)

deg

(2)

where m = 1, 2, ..., P and n = 1, 2, ..., S .

From the Eq. (1), the RAAN is equally spaced by  = 360/P deg in the range m  [0, 360] deg. The intraplane spacing M = 360/S deg generates a symmetric location in the orbital plane in the range M  [0, 360] deg and is equivalent to the relative angular distance between the satellites in the orbital plane. The relative argument of the latitude (u) in the adjacent orbital planes is derived as u = 360/T - F deg from Eq. (2).

Pattern Repetition Period The Walker-Delta pattern has geometric characteristics such that the intra- and inter-plane angular spacings are homogeneous. This geometric symmetry determines the pattern repetition period. The investigation of patterns in a geographical coordinate system enhances the understanding of the pattern repetition period. Reference 4 derived the formulas for the pattern repetition period. The pattern unit (PU), which is introduced to understand the orbital configuration of the Walker-Delta constellation, is defined as follows:2,3

1PU = 360 deg

(3)

T

The RAAN and mean anomaly in Eqs. (1) and (2) are reorganized in PU as

m = S - (m - 1) PU

(4)

Mm,n = F - (m - 1) + P - (n - 1) PU

(5)

The time interval in which the mean anomaly increases for F PU is the first pattern repetition period

tF and defined as

tF

=

F

-

360 T

-

1 orb sec

(6)

where orb denotes the orbital angular speed. Assuming the twobody motion, the RAAN and mean anomaly at tF are derived as

m (tF) = m (t0) = S - (m - 1) PU

(7)

Mm,n (tF) = Mm,n (t0) + F = F - m + P - (n - 1) PU

(8)

= Mm+1,n (t0) PU

where t0 denotes the epoch time.

From Eqs. (7) and (8), the mean anomaly of the nth satellite in mth orbital plane at tF, Mm,n (tF), is the same as the one of the nth satellite in (m + 1)th orbital plane at t0, Mm+1,n (t0). Thus, the constellation pattern observed at tF appears as a pattern at t0 that is shifted westward as  deg.

On the other hand, the mean anomaly propagates P PU during tP and defines the second pattern

repetition period as

tP

=

P

-

360 T

-

1 orb

sec

(9)

3

Figure 2. Walker-Delta patterns in geographic coordinate frame at epoch time, tF, and tP (+: S AT 1,1, : S AT M,1, : the rest satellites)

The RAAN and the mean anomaly at tP are derived as

m (tP) = m (t0) = S - (m - 1) PU

(10)

Mm,n (tP) = F - (m - 1) + P - nPU

(11)

= Mm,n+1 (t0)

Let us define the set of satellites in the mth orbital plane as N = {n | n = 1, 2, ..., S }. Then, Eqs. (10)

and (11) derive

Mm,N (tP) = Mm,N (t0) .

(12)

4

Therefore, the constellation pattern at tP appears identical to the one at t0.
Figure 2 shows the Walker-Delta constellation pattern for i: T/P(S )/F = 42: 120/20(6)/1 in the geographic coordinate frame. The marks are subsatellite points; +, , and represent S AT 1,1, S AT M,1, and the remaining satellites, respectively, where M = {m|m = 1, 2, ..., P} is the set of orbital plane numbers. The blue line represents the bounded Voronoi diagram for the mid-latitude and equatorial regions, which will be described in the next section. S AT 1,1 is barely moved in the middle panel compared to the one in the top panel because tF is only 54 seconds. However, the blue diagrams show that the entire constellation moves westward for  = 18.00 deg. The bottom panel shows the pattern at tP, which is 18 min and 14 s. The position of each satellite in the bottom panel is propagated for tP from the top panel; however, the patterns of the top and bottom panels are the same.
Duplicate Allocation of Orbital Elements The Walker-Delta design method allocates the six unique orbital elements to each satellite, and the six orbital elements correspond to the unique orbital state of the six positions and velocity elements. This suggests the possibility of duplicate satellite positions and implies the collision between satellites. The conditions of the duplicate orbital elements of the Walker-Delta constellation are investigated in reference 4 as

m,n - m,n = 180 deg

(13)

Mm,n - Mm,n = 180 deg .

Equation (13) can be expressed by the Walker-Delta design parameters as follows:

m

=

1

+

P 2

n = mod

1

+

S -F 2

,

S

+ S -  mod

1

+

S -F 2

,

S

,0

.

(14)

where mod (x, y) denotes the modulo operation, which returns the remainder when x is divided by y, and  (x, y) represents the Kronecker delta function, which equals 1 if x = y and 0 otherwise. Therefore, the Walker-Delta design parameters that accommodate Eq. (14) must be avoided in the design procedure.

Common Ground-track Constellation
Repeat Ground-track Orbit The repeat ground-track (RGT) orbit is an orbit that traces the same ground-track within a specific time interval. The two main parameters that determine the RGT orbit are the number of revolutions to repeat (NP) and the number of days to repeat (ND).5 For example, if the number of revolutions to repeat is 14 and the number of days to repeat is 1, the ground-track crosses (ascends or descends) the equator 14 times in one day. Thus, the period ratio (), which is the RGT design parameter, is formulated as

 = NP/ND

(15)

The period ratio can also be described by the satellite nodal period (TS ) and the nodal period of Greenwich (TG). The change in the orbital elements due to J2 effect induces changes in TS and TG

as

TS

=

2  + M

(16)

TG

=

2 E -

(17)

5

where E is Earth's rotation speed. The orbital elements are formulated using Eqs. (18), (19), and (20):

=

3 2 J2

RE p

2

-E a3

2 - 5 sin i2 2

(18)

M =

-E a3

 1

-

3 2

J2

RE p

2

1 - e2

3 2

sin i2

-

1

 

(19)

=

-

3 2

J2

RE p

2

-E 2 cos i p

(20)

Based on the definition of period ratio, Eqs. (16) and (17) derive Eq. (15) with respect to the orbital

elements as:

=

NP ND

=

TG TS

=

 + M E - 

(21)

From Eqs. (18), (19), and (20), the orbital elements have arguments as  =  (a, i, e), M = M (a, i, e), and  =  (a, i, e). It organizes the arguments of TS , TG, and  as:

TS = TS (a, e, i)

(22)

TG = TG (a, e, i)

(23)

 =  (a, e, i)

(24)

From this, the RGT orbital design algorithm can be derived. Given the specific , inclination (i), and eccentricity (e), the algorithm calculates the corresponding semi-major axis (a). Equation (15) implies that  determines the number of revolutions per period and suggests that  is related to the orbital period and semi-major axis. Consequently, when e and i are specified, one unique semimajor axis is derived from  and vice versa. For example, if the set of RGT orbital elements is given as (, i, e) = 14, 42 deg, 0 , then a is 7201.90km. As a result, the RGT orbital elements can be described in two different ways, such as (a, i, e) = 7201.90km, 42 deg, 0 , and then  is uniquely determined as 14.

Common Ground-track Constellation The RGT orbit that is designed according to Eqs. (21) contains a set of (, i, e) or (a, i, e) with an arbitrary set of (, , M). From here on, the orbital elements of the RGT orbit are denoted as (, i, e) except for specific purposes. This implies that a numerous number of satellites can trace the same ground-track and introduces the concept of a common ground-track (CGT) constellation. The CGT constellation is designed following the three procedures below:6,7 (1) Calculate the semi-major axis (a) of the seed satellite from (, i, e) in Eq. (21). (2) Choose an arbitrary  so that all satellites have the same (, i, e, ). (3) Given the CGT constellation's total number of satellites (T ), the kth satellite's RAAN and mean anomaly (k, Mk) satisfy Eq. (25)

NPk + ND Mk = constant mod 2

(25)

where k = 1, ..., T .

The CGT constellation design problem is concluded as the configuration method of (k, Mk) following procedure (3). The reference 7 introduces two methods, quasi-symmetric and binary integer programming (BILP).

6

Quasi-symmetric Method The simulation time (Tsim) is discretized by the step size tstep and is assumed to be an integer multiple of the repetition period. Thus, this can be formulated as Tsim = L - tstep. The continuous time variable t  [0, Tsim] is converted into the discretized time variable   {0, 1, ..., L - 1}. The configuration of the satellites in the CGT constellation can be expressed as
time-shifted seed satellites because all satellites have the same ground-track traces. Therefore, the constellation pattern vector x [] can be defined as follows:

x

[]

1 0

if  = k, otherwise.

(26)

where k is the temporal location of the kth satellite.
In the discretized time domain, the constellation pattern vector has length L. If the total number of constellations is T , then the spacing constant  is defined as follows:

L. T

(27)

If  is an integer, k is equally spaced and the satellites are configured symmetrically. In contrast, if T is not a divisor of L, then  is not an integer that makes the index k a rational number. In this case, only a quasi-symmetric configuration is possible. The formulation for both symmetric and quasi-symmetric constellation pattern vectors x [] is defined as

T

x []   nint ( -  (k - 1))

(28)

k=1

where nint denotes the nearest integer function.

Binary Integer Linear Programming Method Because the domain of the constellation pattern

vector is defined as binary, the BILP method is introduced as an optimization algorithm. The BILP

algorithm is a variant of the linear programming method that optimizes a linearized objective func-

tion with constraints and boundaries. The problem statement of the linear programming can be

generalized as8

min cT x subject to A - x  b

(29)

x

Aeq - x = beq

where x is the decision variable of length L, cT x is the objective function, A  RQ-L and b  RQ are the matrix and vector that constitutes the Q numbers of inequality constraints, Aeq  RR-L and b  RR are the matrix and vector of R numbers of equality constraints.

In addition to Eq. (29), the domain of the decision variable x must be defined. The domain sets R0, Z0, and Z2 induce the pure real and binary integer linear programming. It is also possible for mixed-integer linear programming to include both real and integer decision variables. Thus, the BILP has the same problem statement but constrains the domain of the decision variables as

x  Z2L

(30)

The objective of optimization is to obtain a constellation pattern vector that minimizes the number of satellites while satisfying the coverage requirement. Because the summation of x [] is equal to

7

Figure 3. (a) Geometric relationships between the satellite, coverage edge, and center of the Earth and (b) geometric description of coverage

T by the definition of the constellation pattern vector in Eq. (26), the problem is formulated as

min
x

1T

x

subject

to

V0, x 

jx  Z2L

f

j,

j  J

(31)

where j is the index for the jth grid, J is the set of grids in the area of interest, and Z2 is the binary integer number set. The matrix V0, j  Z2L-L is a seed-satellite access profile circulant matrix, which is addressed in detail in the next section.

COVERAGE ANALYSIS METHODS

Geometry of Earth Coverage

Figure 3a shows the geometric relationships between the satellite, coverage edge, and center of the Earth and is advantageous for coverage analysis. The true horizon is tangential from the satellite to the Earth's surface. The angle between the true horizon and the subsatellite point (SSP) is called the maximum Earth central angle (ECA, 0) or the angular radius of the Earth () when measured from the center of the Earth and the satellite, respectively. When the satellite is located at an altitude of h km, the angular radius of the Earth is determined using Eq. (32):

sin

=

RE RE +

h

(32)

where RE is the Earth's radius.

Usually, the payload's coverage determines the coverage performance of a single satellite that constitutes the constellation. The Earth central angle () measures the size of payload coverage () on the Earth's surface and is defined as the angular distance between the SSP and the coverage edge. The coverage edge is the rim of the satellite coverage on the Earth. The elevation angle () is measured at the coverage edge from the local horizontal to the satellite.

The coverage can be approached from two perspectives: the satellite and the target area (Figure 3b). When considering the satellite perspective, it is important to evaluate payload's specifications. According to the definition of the coverage, the nadir angle ( = (t)) should be smaller than

8

the payload beam coverage (Max). From the target point perspective, it is considered to be covered when the elevation angle of the satellite ( = (t)) is greater than the target point's minimum elevation angle (min).

The trigonometry of the blue shaded triangle in Figure 3a yields the formulae for , , and  as

Eqs. (33) and (34).

cos  = sin / sin 

(33)

 = 90 deg - - 

(34)

For communication constellations, constraints are imposed on both the payload specification and the elevation angle of the target point. Therefore, the trigonometry of Eqs. (33) and (34) is crucial, as it prevents redundant computational complexity. For example, suppose that the beam coverage of the spacecraft (Max) is 45 deg, and the ground station has a minimum elevation angle (min) of 30 deg. If the satellite's altitude is 1, 200 km, the angular radius of Earth () is 57.31 deg. The Eq. (33) immediately converts the payload's coverage to the elevation angle as

 = arccos (sin Max/ sin ) = 32.84 deg

(35)

where  is the elevation angle corresponding to Max and does not have a physical meaning. The ECA () is calculated using Eq. (34) as

 = 90 - Max -  = 12.16 deg

(36)

In the same manner, the minimum elevation angle (min) yields its corresponding parameters as ~ = 46.79 deg and ~ = 13.21 deg. The ECA is the visualized size of the coverage on the Earth's
surface; the smaller the ECA, the more degraded the coverage performance becomes. Therefore, a simulation with only , Max, or  is enough to analyze if the constellation satisfies the coverage requirement. Since the coverage analyses with , Max, or  show the same results but are conducted from different perspectives, the simulation with only one of the three constraints reduces the
computational cost.

Voronoi Tessellation
The problem of a continuous coverage constellation can be reduced to obtaining the circumradius of three adjacent points. For a set of discretized points, the circumradius of three adjacent points can be defined. When the circumradius is smaller than a specified value, the distance from any point within the region is shorter than the specified value. References 2 and 3 introduced the satellite triad method as a coverage analysis technique for Walker constellations. The research subject of the references was a constellation of fewer than 20 satellites. This study utilizes the Delaunay triangulation method, which was first suggested in 4, to generalize the number of satellites in the constellation.
Delaunay triangulation is a computational geometry method that subdivides discretized points into triangles.9 This algorithm defines the Delaunay criterion for constructing Delaunay conformant triangles that do not contain other points inside the circumcircles. The Voronoi diagram (VD) is a dual graph of the Delaunay triangle (DT) and is drawn by connecting the circumcenters of the Delaunay triangles. Voronoi tessellation refers to the tiling of a plane or sphere using Voronoi diagrams. If the tiled region is a restricted closed area on the sphere, the Voronoi diagrams have boundaries cut by the region and are called bounded Voronoi diagrams (BVD).4,10 The constellation

9

Figure 4. Example: (a) Delaunay triangle, (b) Voronoi diagram, and (c) bounded Voronoi diagram

coverage problem can be formulated as a Voronoi tessellation problem. The subsatellite points on the Earth's surface are discretized points on a three-dimensional spherical surface. The area of interest is not the entire globe, and the Voronoi diagram is bounded within the target region. The spherical Delaunay triangles and spherical bounded Voronoi diagrams derive the solution; however, the word `spherical' is omitted for brevity from here on.

Figure 4 depicts examples of the Delaunay triangle, Voronoi diagram, and bounded Voronoi diagram. In Figure 4a, the six DTs contain pk as their vertices for an arbitrary subsatellite point pk, where k = 1, 2, ..., T . DT k,l are depicted as red triangles, and the circumcenters Ck,l are blue dots, where l = 1, 2, ..., Nk. Nk is the number of triangles that have vertices pk and can be different for each pk. Any subsatellite point possesses only one VD, and V Dk is drawn by connecting the blue dots to the circumcenters Ck = Ck,l | l = 1, 2, ..., Nk , as shown in Figure 4b.
The Voronoi diagram in Figure 4b can be used to solve the global coverage problem. However, for the regional coverage problem, the Voronoi diagram must be bounded within the area of interest. In particular, for the regional continuous coverage problem, the Voronoi diagram bounded within the latitude range of the AoI as a circular band can efficiently analyzes the continuity of the constellation.4 Considering the northern area of interest, the bounded Voronoi diagram appears in Figure 4c. Then, pk has BV Dk with different vertices Ck = Ck,l | l = 1, 2, ..., Nk .
The angular distance k,l is defined as the angular distance between the subsatellite point pk and the vertices Ck,l. Then, the maximum distance BV Dk of the kth satellite is expressed as:

max,k = max k,l

(37)

l

Consequently, the maximum angular distance of the entire constellation is obtained as.

max = max max,k

(38)

k

Assuming a homogeneous constellation, the coverage performances of all satellites are the same and can be expressed as . Then, the continuous coverage problem statement is defined as

max  .

(39)

10

For the global coverage problem, the maximum angular distance should be defined from k,l and Ck,l, and the remaining procedures are the same.

APC Decomposition

The reference 7 developed the APC decomposition based on the circular convolution phenomenon between a seed satellite's access profile, a constellation pattern vector, and a coverage timeline. The access profile between the kth satellite and the jth target point (vk, j) defines its elements as follows:

vk,

j

[]

1 0

if k, j []  k, j,min [] otherwise

(40)

where  is the discretized time variable and J is the set of target points.

The coverage timeline of constellation b j is derived as the summation of all access profiles as

follows:
T

b j [] = vk, j []

(41)

k=1

The circular convolution phenomenon expresses the coverage timeline b j with respect to the seed satellite access profile v0, j and the coverage pattern vector x as

b j [] = v0, j []  x []

(42)

where x is defined in Eq. (25) and  denotes the circular convolution operator. This circular convolution operation can be described in a linearized form as follows:

b j = V0, jx

(43)

where V0, j is the matrix in Eq. (31).
In summary, the coverage timeline of the entire constellation is obtained from the circular convolution of the seed satellite access profile and the constellation pattern vector. This concept of APC decomposition reduces the optimal CGT constellation design problem to a constellation pattern vector optimization problem.

RELATIVE MOTION IN ADJACENT ORBITAL PLANES

The satellites in the adjacent orbital planes S AT m,n and S AT m+1,n have the angular distances in terms of the differential RAAN and mean anomaly as

u

=

Mm+1,n

-

Mm,n

=

360 T

-

F

deg

(44)

=

m+1,n

- m,n

=

360 P

deg

(45)

Since the Walker-Delta constellation satellites are designed to have the same altitude and inclination, the relative motion between S AT m+1,n and S AT m,n can be described analytically.11 The minimum and maximum relative angular distances (min and max) are formulated as follows:

sin (min/2) = sin (R/2) cos (iR/2)

(46)

11

Figure 5. Relative motion of the satellites in the adjacent orbital planes

cos (max/2) = cos (R/2) cos (iR/2)

(47)

where iR is the relative inclination and R is the relative phase.

The relative inclination iR in Figure 5 is the angle between the orbital planes measured at the orbital intersection and is derived from spherical trigonometry as

cos iR = cos i2 + sin i2 cos 

(48)

 iR = iR (i; P)

where Eq. (45) is used.

The spherical triangle in Figure 5 derives the geometric relationship between the relative phase R and the angular distances m and m+1 as follows:

m + R - m+1 = 180 - 2m+1

(49)

where the spherical trigonometric rule that the differential arc between the intersected orbits is 180 - 2m+1 is used. The relative phase R is obtained by reorganizing Eq. (49)

R = 180 - 2m+1 + (m+1 - m)

(50)

= 180 - 2m+1 + u

where the differential angular distance m+1 - m is the relative argument of the latitude u in the Walker-Delta constellation. The formula to calculate m+1 is

tan m+1

=

tan (90 - /2) cos i

(51)

 m+1 = m+1 (i; P)

As a result, Eq. (51) provides the argument of R as follows:

R = R (i; T, P, F)

(52)

12

Figure 6. Bounded Voronoi diagram result of Walker-Delta constellation (i: T = 42: 40)
The inter-satellite link (ISL) constrains the range of relative motion so that the signal is not interfered within the link margin. Therefore, the minimum and maximum relative distances in Eqs. (46) and (47) within the specified range guarantee a smooth ISL communication.
The relative motion of the adjacent orbital plane is described in Eqs. (48), (50), and (51) and explains the relative motion between S AT m,n and S AT m+1,n where m = 1, ..., P - 1 and n = 1, ..., S . When m = P, the relative motion between S AT P,n and S AT 1,n+F is proven to be the same as the one between S AT m,n and S AT m+1,n by Eqs. (1), (2), (48), (50) and (51). As a result, if Eqs. (46) and (47) satisfy the constraint on the ISL link, then all ISL links are connected without any isolated links.
SIMULATION RESULTS
Continuous Coverage Analysis
The constellation is designed using the three constellation design methods introduced in the previous sections: Walker-Delta constellation, quasi-symmetric CGT, and BILP CGT constellations. The seed satellites for the three constellations are designed to have the repetition period of  = 14/1. The inclination is 42 deg which is 3 deg -5 deg higher than the area of interest.12,13 The minimum elevation angle min is 15 deg and the target point is located in Seoul. The Walker-Delta constellation is analyzed assuming twobody motion, and the target area is a circle with a radius of 100 km around Seoul. The CGT constellations assume J2 perturbation and a single target point. The sampling time or time step tstep is 1 and 300 s for the Walker-Delta and CGT constellations, respectively, and the simulation time horizon is 1 day for both.
Walker-Delta Constellation Figure 6 depicts the bounded Voronoi diagram simulation result of the Walker-Delta constellation. The global search of a smaller number of satellites obtains that 40 satellites at an inclination of 42 deg is the minimum number of satellites required to achieve the continuous coverage using the Walker-Delta constellation. The empty circles represent the T/P/F
13

parameters with duplicate positions in Eq. (14) and are precluded from the coverage analysis. The empty diamond markers indicate that the parameters did not achieve the continuous coverage. The continuous coverage solution is i: T/P(S )/F = 42: 40/40(1)/30 and denoted as the black diamond. The ECA of this solution () is 15.86 deg.
Figure 7. Configurations of quasi-symmetric and BILP CGT constellations in (, M) space
Figure 8. APC Decomposition of (a) quasi-symmetric and (b) BILP CGT constellation 14

Figure 9. Relative motion between the adjacent orbital plane of Walker-Delta constellation (i: T = 42: 40)

Common Ground-track Constellation The quasi-symmetric constellation pattern vector xqs and BILP constellation pattern vector xbilp are obtained as

xqs

=

1 0

for n = {0, 9, 18, 27, 36, 45, 54, 63, 72, 81, 90, 99, 108, 117, 126, 135, ... 144, 153, 162, 171, 180, 189, 198, 207, 216, 225, 234, 243, 252, 261, 270, 279} otherwise

(53)

xbil p

=

1 0

for n = {9, 14, 22, 27, 29, 55, 60, 63, 68, 96, 101, 104, 109, 114, 137, ... 142, 150, 155, 175, 183, 188, 191, 216, 221, 224, 229, 232, 257, 262, 265, 270} otherwise

(54)

The CGT constellation's pattern reveals its characteristics in the (, M) space, such as period ratio and symmetricity (Figure 7). The gradient of the admissible set is -NP/ND and is equal to - by Eqs. (25) and (15). The constellation pattern vectors are laid on the points along the admissible set. The quasi-symmetric set configures symmetrically in Figure 7 as xqs in the second panel of Figure 8a is equally spaced. Because Nqs is 32 and L is 288, L/Nqs is divided into an integer 9, and the spacing is perfectly symmetric. On the other hand, the BILP constellation pattern vector is irregularly spaced in Figures 7 and 8b. However, the BILP constellation achieves the smaller number of satellites Nbilp as 31, while both constellations exhibit the single-fold coverage.

Inter-satellite Link Continuity Analysis
Walker-Delta Constellation The minimum and maximum relative distances are the line distances calculated from the angular distances in Eqs. (46) and (47) (Figure 9). The upper and lower bounds of the bars indicate the relative distance ranges in the adjacent orbital planes. The colors of the bars

15

distinguish the number of planes, and the x axis represents the F numbers. As this graph shows the relative motion at a glance, it is a useful tool for ISL connectivity analysis. The continuous coverage solution i: T/P(S )/F = 42: 40/40(1)/30 has a relative motion range from 9559.77 km to 9589.64 km.

Common Ground-track Constellation The relative motion equations, Eqs. (48), (50), and (51),
imply that the relative motion of two orbits with the same altitude and inclination is a function of
the inclination, relative RAAN, and relative argument of latitude. Let us define a set of temporal location k in Eq. (26) as k. Then, k,qs and k,bilp are calculated as Eqs. (53) and (54). The temporal location k derives the RAAN k as shown in Eq. (55).7

k

=

k

-

2ND L

+

0

(55)

where the subscript `0' means that the variable is relevant to the seed satellite. Equation (25) describes the relationship between k and Mk.
Let us define k as the difference between consecutive k values:

k

=

k+1 k +

- L

k - 1

for k = 1, ..., T - 1 for k = T

(56)

Thus, Eqs. (53), (54), and (56) are used to calculate k for the two CGT constellations as

k,qs = 9

(57)

k,bilp = 2, 3, 5, 8, 20, 23, 25, 26, 27, 28

(58)

Figure 10. Minimum and maximum relative distance between the adjacent orbital plane of quasi-symmetric and BILP CGT constellations
16

Equation (55) derives the relative RAAN k and the relative mean anomaly Mk as

k,qs = 11.25 deg

(59)

Mk,qs = 202.50 deg

Mkk,,bbiillpp

= =

2.5, 3.75, 6.25, 10.00, 25.00, 28.75, 31.25, 32.50, 33.75, 35.00 deg 10.00, 220.00, 230.00, 247.50, 265.00, 272.50, 282.50, 307.50, ...
317.50, 325.00 deg

(60)

The minimum and maximum relative distances in Eqs. (46) and (47) are depicted in Figure 10. The minimum and maximum relative distances appear almost identical for some cases because the differences are less than 1000 km. The minimum and maximum relative distances for the quasisymmetric CGT constellation are 13854.32 and 13886.49 km, respectively. The BILP CGT constellation has various values of k. When k is 8, the minimum and maximum relative distances reach their largest values at 13164.56 and 13191.33 km, respectively.

CONCLUSION
This paper investigates the continuous coverage analysis methods and the inter-satellite link connectivity analysis method for communication satellite constellations. The bounded Voronoi diagram is used to design a homogeneous constellation that ensures continuous regional and global coverage. The APC decomposition, based on the grid method, can be implemented for the CGT constellation's coverage analysis. The relative motion in adjacent orbital planes yields the analytical solutions that must be constrained within the inter-satellite link range.
The coverage performance of the Walker-Delta constellation was analyzed using the bounded Voronoi diagram as an example. Two types of CGT constellations, the quasi-symmetric and the BILP, were analyzed using APC decomposition to compare their coverage performance. The BILP optimal CGT constellation has an asymmetric configuration but achieves a smaller number of satellites. However, the relative motion range of the Walker-Delta constellation is shorter and more consistent, which implies that the Walker-Delta constellation has advantages for inter-satellite links. The relative motion of the BILP constellation has a variety of ranges due to its asymmetry, but satellites are located closer than the quasi-symmetric constellation. In summary, the BILP constellation is advantageous in terms of the number of satellites required for a single-fold coverage. However, the Walker-Delta constellation may have a shorter and more stable relative motion range, which is beneficial for inter-satellite links.

ACKNOWLEDGMENT
This work was supported by the Korea Research Institute for defense Technology Planning and Advancement (KRIT) grant funded by the Korean government (DAPA (Defense Acquisition Program Administration)) (KRIT-CT-22-040, Heterogeneous Satellite Constellation-based ISR Research Center, 2024).

17

NOTATION

a b  e f i f h j J2 J
k L m n NP ND P F RE p -E S T Tr TS TG T sim tstep t t0 tF, tP u v V x
Z2        
E orb
  

semi-major axis

coverage timeline

Kronecker delta function

eccentricity

coverage requirement vector

inclination

coverage requirement

altitude

index for grid point

coefficient for J2 perturbation

set of grid points

index for satellites

number of discrete times (length of discrete time variable)

index for orbital planes

index for satellites on a plane

revolutions to repeat

days to repeat

number of orbital planes

Phasing parameter

Earth radius

semilatus rectum

standard gravitational parameter of Earth

number of satellites on an orbital plane

total number of satellites

repetition period of RGT orbit

nodal period of the satellite

nodal period of greenwich

simulation time

time step

continuous time variable

epoch time

Walker-Delta pattern repetition period

argument of latitude

access profile

access profile circulant matrix

constellation pattern vector

binary integer number set

elevation angle

angular size of payload's coverage

angular radius of Earth

Earth central angle

period ratio

phase angle

discretized time variable

argument of perigee

Earth rotation speed

orbital angular speed

right ascension of ascending node

spacing constant

angular distance

18

REFERENCES [1] I. d. Portillo, B. G. Cameron, and E. F. Crawley, "A technical comparison of three low earth orbit satellite
constellation system to provide global broadband," Acta Astronautica, Vol. 159, 2019, pp. 123-135. [2] J. G. Walker, "Circular Orbit Patterns Providing Continuous Whole Earth Coverage," Technical rept.,
1970, pp. 19-23. [3] J. G. Walker, "Continuous Whole-Earth Coverage by Circular-Orbit Satellite Patterns," Technical rept.,
1977, pp. 3-26. [4] S. Jeon, S.-Y. Park, K. H. Lee, and K.-S. Jeong, "Communication Satellite Constellation Design of
Minimum Number of Satellites: Analytic Approach to Walker-Delta Pattern Design," Journal of the Korean Society for Aeronautical and Space Sciences, Vol. 52, No. 9, 2024, pp. 749-760. [5] D. A. Vallado, Fundamentals of Astrodynamics and Applications. Microcosm and Springer, 2013. [6] M. E. Avendan~o, J. J. Davis, and D. Mortari, "The 2-D Lattice Theory of Flower Constellations," Celestial Mechanics and Dynamical Astronomy, Vol. 116, No. 4, 2013, pp. 325---337. [7] H. W. Lee, S. Shimizu, S. Yoshikawa, and K. Ho, "Satellite Constellation Pattern Optimization for Complex Regional Coverage," Journal of Spacecraft and Rockets, Vol. 57, No. 6, 2020, pp. 1309-1327. [8] M. Conforti, G. Cornueljols, and G. Zambelli, Integer Programming. 2014. [9] D. Boris, "Sur la sphere vide," Bulletin de l'Acade-mie des Sciences de l'URSS, Classe des Sciences Mathe-matiques et Naturelles, Vol. 6, 1934, pp. 793-800. [10] G. Dai, X. Chen, M. Wang, E. Fernandez, T. N. Nguyen, and G. Reinelt, "Analysis of Satellite Constellations for the Continuous Coverage of Ground Regions," Journal of Spacecraft and Rockets, Vol. 54, No. 6, 2017, pp. 1294-1303. [11] J. R. Wertz, Orbit and constellation design and management. Springer, NewYork, 2009. [12] J. R. Wertz, "Coverage, Responsiveness, and Accessibility for Various 'Responsive Orbits'," 3rd Responsive Space Conference, 2005. [13] X. Fu, W. Meiping, and T. Yi, "Design and Maintenance of Low-Earth Repeat-Groundtrack SuccessiveCoverage Orbits," Journal of Guidance, Control, and Dynamics, Vol. 35, No. 2, 2012, pp. 686-691.
19

