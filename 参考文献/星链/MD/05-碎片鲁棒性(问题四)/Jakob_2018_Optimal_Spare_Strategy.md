---
title: "Optimal Constellation Spare Strategy Using Multi-Echelon Inventory"
author: Jakob, Ho
year: 2018
journal: J. Spacecraft and Rockets
doi: 10.2514/1.A34387
type: 参考文献
subject: 数学建模-星链系统
topics:
  - 备份策略
  - 多级库存
  - 星座冗余
parser: mineru
---

# Optimal Satellite Constellation Spare Strategy Using Multi-Echelon Inventory Control

Pauline Jakob

University of Illinois at Urbana-Champaign, Urbana, Illinois 61801

Seiichi Shimizu<sup>†</sup> and Shoji Yoshikawa<sup>†</sup>

Mitsubishi Electric Corporation, Amagasaki 661-8861, Japan

and Koki Ho<sup>‡</sup>

University of Illinois at Urbana-Champaign, Urbana, Illinois 61801

DOI: 10.2514/1.A34387

The recent growing trend to develop large-scale satellite constellations (i.e., mega-constellations) with low-cost small satellites has brought the need for an efficient and scalable maintenance strategy decision plan. Traditiona spare strategies for satellite constellations cannot handle these mega-constellations due to their limited scalability in the number of satellites and/or frequency of failures. This paper proposes a novel spare strategy using an inventory management approach. It considers a set of parking orbits at a lower altitude than the constellation orbits for spare storage, and models the satellite constellation spare strategy problem using a multi-echelon $( s , Q ) \mathrm { - t y p e }$ inventory policy, viewing the Earth s ground as a supplier, the parking orbit spare stocks as warehouses, and the in-plane spare stocks as retailers. The accuracy of the proposed analytical model is assessed using simulations via Latin Hypercube Sampling. Furthermore, based on the proposed model, an optimization formulation is introduced to identify the optimal spare strategy, comprising the parking orbits characteristics and all locations policies, to minimize the maintenance cost of the system given performance requirements. The proposed model and optimization method are applied to a real-world satellite mega-constellation case to demonstrate their value.

## Nomenclature

<table><tr><td> $D_{\text{parking}}$ </td><td>=</td><td>demand for parking spares, in units of batches  $Q_{\text{plane}}$ </td></tr><tr><td> $D_{\text{plane}}$ </td><td>=</td><td>demand for in-plane spares, in units of satellites</td></tr><tr><td> $ES_{\text{parking}}$ </td><td>=</td><td>expected number of backorders for parking spares over a replenishment cycle, in units of batches  $Q_{\text{plane}}$ </td></tr><tr><td> $ES_{\text{plane}}$ </td><td>=</td><td>expected number of backorders for in-plane spares over a replenishment cycle, in units of satellites</td></tr><tr><td> $f_{\text{parking}}$ </td><td>=</td><td>probability density function of the lead time to the parking orbits, in units of days $^{-1}$ </td></tr><tr><td> $f_{\text{plane}}$ </td><td>=</td><td>probability density function of the lead time to the constellation orbits, in units of days $^{-1}$ </td></tr><tr><td> $h_{\text{parking}}$ </td><td>=</td><td>altitude of the parking orbits, in units of kilometers</td></tr><tr><td> $h_{\text{plane}}$ </td><td>=</td><td>altitude of the constellation orbits, in units of kilometers</td></tr><tr><td>i</td><td>=</td><td>inclination of the constellation orbits, in units of degrees</td></tr><tr><td> $k_{Q,\text{parking}}$ </td><td>=</td><td>order batch size for parking spares, in units of batches  $Q_{\text{plane}}$ </td></tr><tr><td> $k_{s,\text{parking}}$ </td><td>=</td><td>safety stock for parking spares, in units of batches  $Q_{\text{plane}}$ </td></tr><tr><td> $m_{\text{dry}}$ </td><td>=</td><td>dry mass of the satellites, in units of kilograms</td></tr></table>

<table><tr><td> $m_{\text{fuel}}$ </td><td>=</td><td>fuel mass required for a Hohmann transfer (from a parking orbit to a constellation orbit), in units of kilograms</td></tr><tr><td> $N_{\text{days}}$ </td><td>=</td><td>number of days per year</td></tr><tr><td> $N_{\text{fail,parking}}(\tau)$ </td><td>=</td><td>demand for parking spares during a lead time  $\tau$ , in units of batches  $Q_{\text{plane}}$ </td></tr><tr><td> $N_{\text{fail,plane}}(\tau)$ </td><td>=</td><td>demand for in-plane spares during a lead time  $\tau$ , in units of satellites</td></tr><tr><td> $N_{\text{parking}}$ </td><td>=</td><td>number of parking orbital planes</td></tr><tr><td> $N_{\text{plane}}$ </td><td>=</td><td>number of constellation orbital planes</td></tr><tr><td> $N_{\text{sats}}$ </td><td>=</td><td>number of operational satellites per orbital plane in the constellation</td></tr><tr><td> $P_{\text{av}}$ </td><td>=</td><td>parking orbit availability</td></tr><tr><td> $P(i^{\text{th}})$ </td><td>=</td><td>probability of getting supply from the  $i$ th closest parking orbit</td></tr><tr><td> $p_{\text{launch,full}}$ </td><td>=</td><td>cost of a full rocket launch (for  $U_{\text{launch}}$ ), in units of million US$ per launch</td></tr><tr><td> $p_{\text{holding}}$ </td><td>=</td><td>annual holding cost of a satellitet, in units of million US$ per satellite per year</td></tr><tr><td> $p_{\text{launch}}$ </td><td>=</td><td>launch cost, in units of million US$ per launch</td></tr><tr><td> $p_{\text{sat}}$ </td><td>=</td><td>manufacturing cost of unit satellite, in units of million US$ per satellite</td></tr><tr><td> $p_{\text{launch,unit}}$ </td><td>=</td><td>cost of a unique satellite rocket launch (for one satellite only), in units of million US$ per launch</td></tr><tr><td> $Q_{\text{parking}}$ </td><td>=</td><td>batch size for parking spares, in units of satellites</td></tr><tr><td> $Q_{\text{plane}}$ </td><td>=</td><td>batch size for in-plane spares, in units of satellites</td></tr><tr><td> $s_{\text{parking}}$ </td><td>=</td><td>reorder point for parking spares, in units of satellites</td></tr><tr><td> $s_{\text{plane}}$ </td><td>=</td><td>reorder point for in-plane spares, in units of satellites</td></tr><tr><td> $\overline{SL_{\text{parking}}}$ </td><td>=</td><td>mean stock level of parking spares, in units of batches  $Q_{\text{plane}}$ </td></tr><tr><td> $\overline{SL_{\text{plane}}}$ </td><td>=</td><td>mean stock level of in-plane spares, in units of satellites</td></tr><tr><td> $T_{\text{parking}}$ </td><td>=</td><td>lead time to the parking orbits, in units of days</td></tr><tr><td> $T_{\text{plane}}$ </td><td>=</td><td>lead time to the constellation orbits, in units of days</td></tr></table>

$T_{processing}$ = order processing time for launch, in units of days $U_{launch}$ = launch capacity (number of possible satellites per rocket), in units of satellites $\lambda_{parking}$ = demand rate for parking spares, in units of batches $Q_{plane}$ per day $\lambda_{plane}$ = demand rate for in-plane spares, in units of satellites per day $\lambda_{sat}$ = failure rate of a satellite, in units of failures per year $\mu_{launch}$ = mean time between launches to the parking orbits, in units of days $\rho_{parking}$ = order fill rate for parking spares $\rho_{plane}$ = order fill rate for in-plane spares $v_{ex}$ = effective exhaust velocity of the satellite thrusters, in units of kilometers per second $\epsilon_{maneuvering}$ = fuel mass conversion coefficient, in units of million US\$ per kilograms

## I. Introduction

HE trend for satellite constellations has been growing since their first establishment about 20 years ago, in May 1997 for Iridium and February 1998 for Globalstar. Various studies have been performed with their focuses on optimization of satellite constellation design [1–4]. More recently, new constellations comprising a tremendous number of small satellites (i.e., mega-constellations) have been considered to respond to the explosive demand for telecommunication services. For example, OneWeb is setting up a 900-satellite constellation in a low Earth orbit (LEO) to provide broadband services (see Fig. 1) [5], whereas SpaceX is planning a mega-constellation of nearly 12,000 interlinked broadband Internet satellites [6,7].

To ensure the prosperity of the providers, guaranteeing a high level of customer satisfaction is paramount. Indeed, as discussed by Diekelman [8], the satellite failure mitigation can take a few days to several weeks, and the impact of a failed satellite can affect not only the current lost revenue but also the reputation of the system, and thus its future revenue. Therefore, it becomes vital to maintain the operational state of the system and secure a minimum availability to provide the offered services by avoiding outages. In the case of Iridium, for instance, 20 of the original satellites launched have required replacement, and spare satellites represent a substantial part of the constellation with about 30% of the original fleet [9]. As the trend for satellite mega-constellations grows, a large number of satellite failures can be expected from future mega-constellations, and a steady replacement strategy has to be established to maintain the service level.

Existing satellite constellation spare strategies are not effective for large-scale small satellite constellations. Traditional spare strategies include having some ground spare satellites to replace the failed satellites using on-demand launch, or having a few active or inactive spare satellites in every orbital plane for redundancy [10]. Although these approaches were acceptable for small-scale constellations with large and highly reliable satellites (i.e., infrequent failures), they are not effective for mega-scale small satellite constellations, where each satellite tends to display less redundancy and thus less reliability to favor cost efficiency. Indeed, using only in-plane spares could result in need for a large number of spare satellite units per orbital plane, thus involving a very high spare strategy cost. On the contrary, launching spare satellites on demand is a risky strategy, given the uncertainties in launch time schedule and the high satellite failure rate. Moreover, the launch of spare satellites itself can be problematic as typical rockets load tens of small satellites (e.g., 150 kg per satellite for OneWeb’s constellation [11]) per launch, leveraging the batch launch discount (i.e., the cost-saving effects by launching many satellites in one rocket); we cannot provide on-demand launches fo every spare satellite at a low cost. Some companies have foreseen the replenishment of their constellation-to-be, such as OneWeb, who signed a contract with Virgin Galactic to use their LauncherOne vehicle to haul up one satellite at a time. Yet, the solution adopted by OneWeb would raise the spare launch cost to be approximately seven times higher than that of a nominal satellite launch.<sup>§</sup> Therefore, it is beneficial if we could optimally take advantage of the batch launch discount, which was not possible in the traditional approaches. There is a growing demand to have an automatic and scalable decision making and planning strategy under the uncertainty of satellite failures, in order to ensure the maintenance of the system.<sup>¶</sup>

![](../../images/images_Jakob_2018_Optimal_Spare_Strategy/60c5b9942ac62e10b342afc818a2287e1529acde7be3295c26241f65070609f8.jpg)  
Fig. 1 OneWeb satellite constellation [5].

This paper offers a novel and unique design technique that is scalable for mega-scale satellite constellation replacement strategies leveraging inventory management methods. Our solution is to incorporate a set of parking orbits at a lower altitude than the constellation orbits to save on launch cost, and optimize the spare strategy as a supply chain between the Earth’s ground (supplier), the parking orbits (warehouses), and the constellation orbits (retailers). A multi-echelon inventory control system is considered, under stochastic demands and lead times, comprising one supplier (Earth’s ground), multiple warehouses (the parking orbits with parking spares), and multiple retailers (the constellation orbits with in-plane spares). An <sup>s;</sup> <sup>Q</sup> -type inventory policy is considered so that the <sup> </sup>system can optimally leverage the batch launch discount. An analytical model for the constellation spare strategy is developed in this paper, and an optimization formulation is introduced to optimize the spare strategy, minimizing the maintenance cost of the constellation. The developed optimization formulation can quickly approximate the optimal spare strategy without relying on computationally costly simulations; if necessary, the resulting optimized strategy can be further analyzed with high-fidelit simulations.

Although this paper mainly focuses on satellite systems, the general model developed in this paper also extends the existing inventory management literature. The interesting property of our problem is the specific interactions between the different levels of inventory on demand, lead times, and supply allocation. Particularly, our problem is unique in that its multiple warehouses (the parking orbits) drift over time with respect to multiple retailers (the constellation orbits) due to orbital mechanics effects, and the retailers choose the closest (i.e., defined as the minimum waiting time in this paper) available warehouse at the time of delivery. The general framework allowing retailers to get supplies from different warehouses can provide flexibility to avoid, or at least reduce, stock-out times. The accuracy of the analytical model developed in this paper is assessed using simulations, and the model is then leveraged for optimization of the spare strategy. The proposed model and optimization formulation are applied to a real-world satellite mega-constellation case to demonstrate their value.

The remainder of the paper is organized in the following way. Section II presents an overview of the related literature from both the optimal satellite constellation spare strategy and supply chain model points of view. Section III provides the reader with preliminaries about the general theory of satellite constellations and inventory management useful for the understanding of the model further developed in Sec. IV. Section V assesses the accuracy of the developed analytical model using simulations. In Sec. VI, the optimization of the spare strategy is presented, and Sec. VII provides a case study for the maintenance of a LEO communication satellite mega-constellation along with a sensitivity analysis for different satellite failure rates. Finally, Sec. VIII concludes the paper.

## II. Literature Review

The literature regarding modeling of satellite constellations and their spare strategies is very sparse. Different solutions have been examined to ensure the replacement of failed satellites in orbit for such constellations. Lang and Adams [13], Lansard and Palmade [14], Palmade et al. [15], and Cornara et al. [16] all proposed global constellation design including analysis of their replacement strategies, choosing between distinct spare strategies including ground spares, parking orbit spares, in-plane spares, and overpopulated planes. However, no mixtures of each strategy have been considered, leaving the decision makers little flexibility in spare strategies. Also, the complexity of such systems often leads authors to use simulations to evaluate the satellite reliability or constellation availability over time. However, the use of Monte Carlo simulations [16] can result in computational inefficiency, especially in the case of mega-scale constellations.

Other proposed models handled the simulation issue by adopting an analytical point of view and represented the satellite constellations by an exhaustive number of states; however, most of these models have significant scalability issues. Ereau and Saleman [17] approached the availability issue of satellite constellations using Petri nets, but in order to properly incorporate the use of time, the analytical results would still face the issue of state space explosion. Sumter [18] established an analytical model to find an optimal satellite replacement policy by the means of finite-horizon Markov decision processes, minimizing the expected monetary and opportunity costs of maintaining the constellation. The author limits the state explosion issue raised by Ereau and Saleman by setting several assumptions regarding satellites and their operation, such as zero launch lead time and only considering ground spares. Those suppositions can be questionable and Sumter also recognizes the limitations in the work. Furthermore, the number of states considered for the solution regarding the size of the constellation still remains very large especially for a mega-constellation, with, for example, 4608 states for a constellation comprising 9 satellites. Kelley and Dessouky [19] also used Markov models to evaluate the life cycle cost of a satellite system comprising acquisition, replenishment, and operations costs, linked to a performance model to assess the availability of the service. Again, this type of modeling leads to state explosion as the size of the constellation increases, and thus is not scalable to planned mega-constellations.

There have been very few attempts to model the orbiting satellite constellation spare strategy problem using an inventory management approach. Dishon and Weiss [20] originally analyzed the problem of satellite replenishment from a simple satellite-level perspective and solved it using a classical <sup>N; M</sup> inventory system. Their solution <sup> </sup>monitors the total number of functional satellites in a given system, and when the latter falls from <sup>M</sup> to <sup>N</sup>, replenishment launches are initiated to repopulate the system up to level <sup>M</sup>. An optimal policy was derived using a number-of-satellites-launched-over-time cost function. However, the considered inventory model was very simple and presented several limitations: the replenishment up to a level <sup>M</sup> does not allow consistent launch planning over time; it cannot reflect the reality of batch launch discount and it does not explicitly consider the use of parking orbits. These limitations make the proposed strategy ineffective for large-scale satellite constellations.

Although very few authors developed a satellite constellation replenishment policy leveraging inventory management techniques, the general problems of spare parts inventory control and supply chain management have been studied widely in the literature. Many mathematical models have been proposed over time for supply chain inventories. Multi-echelon systems are particularly interesting for the purpose of satellite constellation spare strategies, and different papers have tried to grasp the complex interactions between different levels of such systems subject to various features. A detailed review can be found in Ref. [21]. In this impetus, Ganeshan [22] followed the work of Deuermeyer and Schwarz [23] and developed a model for multilevel inventory comprising multiple retailers, one warehouse, and multiple identical suppliers while taking advantage of order splitting policies. Various applications of multilevel inventory policies can also be found in the literature. Costantino et al. [24] presented an example of spare parts allocation using multi-echelon inventory control applied to the aeronautical industry, a very demanding sector in terms of availability requirements, while Caglar et al. [25] developed a continuous review, base stock policy for a two echelon, multi-item spare parts inventory system for electronic machines. However, no model has been proposed and studied to address our unique challenge in the satellite constellation spare strategy, which requires multiple warehouses drifting over time, all able to resupply all the retailers and with stochastic demands at the retailers.

To address this significant literature gap, our approach regarding the spare strategy for satellite constellations aims at concurrently considering different levels of spare satellites in the system, including ground spares, parking spares, and in-plane spares, and optimizes the whole supply chain using an analytical model with no need for simulations.

## III. Preliminaries

The analysis in this paper builds upon concepts from two different fields: satellite constellations and inventory management. This section provides the readers with an appropriate description of the enabling notions needed to understand the concepts of satellite constellations and inventory management in the context of this paper.

## A. Satellite Constellation

This subsection presents the theory of orbit perturbations, orbital transfers, and satellite constellations. Only the key elements relevant to this paper are explained here, and further theory can be found in Ref. [26].

## 1. Orbit Perturbations

To analyze the satellite constellation, we need to model the orbit of satellites orbiting the Earth. Only circular orbits are explored in this paper. The classical two-body orbital dynamics relies on the approximation that the Earth is a point mass; however, various factors can cause perturbations to the motion of satellites in reality. Two largest perturbations affecting a satellite’s motion about the Earth are the atmospheric drag and the effects of Earth’s oblateness. At the altitudes considered in this research (≥700 km), atmospheric drag is considered to have negligible effects on the motion; however, the effects of Earth’s oblateness are not negligible.

The oblateness of the Earth causes the irregularity in the gravitational field: the mass spinning creates an extra bulge around the equator, further causing perturbations to the satellite’s orbital motion. This oblateness is characterized by a constant, $J _ { 2 } = 0 . 0 0 1 0 8 2 6 3$ , contributing to a perturbing acceleration and <sup></sup>disturbing the orbital elements. One of the principal effects of the Earth oblateness disturbance that is relevant to our research is to cause the right ascension of the ascending node (RAAN) Ω of an orbit to drift over time, with a rate depending only on the semimajor axis <sup>a</sup> of this particular orbit and its inclination <sup>i</sup>:

$$
\frac {d \Omega}{d t} = - \frac {3 n R _ {\mathrm{Earth}} ^ {2} J _ {2}}{2 a ^ {2}} \cos i\tag{1}
$$

where $n = \sqrt { ( \mu / a ^ { 3 } ) }$ is the mean motion of the satellite, $\mu$ is the <sup>  </sup>standard gravitational parameter of the Earth, and $R _ { \mathrm { E a r t h } }$ is the (mean)

radius of the planet Earth. Note that <sup>a</sup> is a function of the altitude; therefore this change of RAAN depends on the altitude of the orbit.

## 2. Orbital Transfer

To deliver a spare from one orbit (e.g., a parking orbit) to another orbit (e.g., a constellation orbit), we need to consider an orbital transfer. In this study, we consider Hohmann transfers, a common fuel-efficient type of chemical transfer for coplanar circular orbits. Out-of-plane maneuvers are excluded in this paper due to their cost inefficiency. In a Hohmann transfer, the cost of the transfer is evaluated through the mass of fuel $m _ { \mathrm { f u e l } }$ required to perform the transfer, which depends on the velocity variation $\Delta V _ { \mathrm { H o h m a n n } }$ needed to move the satellite from an orbit altitude to another, the effective exhaust velocity $v _ { \mathrm { e x } }$ of the thruster, and the dry mass $m _ { \mathrm { d r y } }$

$$
m _ {\text { fuel }} = m _ {\text { dry }} (e ^ {(\Delta V _ {\text { Hohmann }} / v _ {\text { ex }})} - 1)\tag{2}
$$

where $\Delta V _ { \mathrm { H o h m a n n } }$ can be calculated based on the radius $( \mathrm { i . e . , }$ semimajor axis) of the initial orbit $a _ { 0 }$ and the final orbit $a _ { 1 } \left( a _ { 1 } > a _ { 0 } \right)$ in the context of this paper) as follows<sup>\*\*</sup>:

$$
\Delta V _ {\text { Hohmann }} = \sqrt {\frac {\mu}{a _ {0}}} \left(\sqrt {\frac {2 a _ {1}}{a _ {0} + a _ {1}}} - 1\right) + \sqrt {\frac {\mu}{a _ {1}}} \left(1 - \sqrt {\frac {2 a _ {0}}{a _ {0} + a _ {1}}}\right)\tag{3}
$$

The time of flight of such a Hohmann transfer corresponds to half a period of the transfer ellipse of the semimajor axis $( a _ { 0 } + a _ { 1 } ) / 2$ :

$$
T O F _ {\mathrm{Hohmann}} = \pi \sqrt {\frac {(a _ {0} + a _ {1}) ^ {3}}{8 \mu}}\tag{4}
$$

## 3. Satellite Constellation

A satellite constellation is a set of satellites working together in order to provide a service. When the number of satellites comprised in the system becomes very large, we denote it as a mega-constellation. The well-known Walker Delta pattern constellation [27] is considered in this paper. In this configuration, the total number of satellites is allocated to $N _ { \mathrm { p l a n e s } }$ circular orbital planes (i.e., referred to as the constellation orbits) such that there are $N _ { \mathrm { s a t s } }$ satellites per plane. All constellation orbits share the same altitude $h _ { \mathrm { p l a n e } }$ and the same inclination <sup>i</sup>, and their RAANs Ω are distributed such that the planes are equally spaced $( \Omega _ { k \mathrm { { \cdot t h } \ p l a n e } } = ( k - 1 ) \times ( 2 \pi / N _ { \mathrm { { p l a n e s } } } ) )$ This <sup>    </sup>strategy is of particular interest to preserve the geometry of the system, as all satellites would endure approximately the same orbit perturbations. In other words, all satellites in the constellation would experience the same RAAN drift rate.

Therefore, two constellations with the same inclination but different altitudes (e.g., the constellation orbits and the parking orbits) would have two distinct nodal shift rates $d \Omega / d t$ , and thus we can observe a relative RAAN drift between them. The spare strategy model used in this paper takes advantage of this specific relative

RAAN drift between the constellation orbits and the parking orbits, the latter of which are located at a lower altitude.

## B. Inventory Management

Inventory management considers the flow of products (e.g., spare parts in our context) in a supply chain and enables delivery of a bette service. It encompasses the relations between all levels of inventory, from suppliers to warehouses and to retailers. Inventory control is of primary importance, especially for stochastic demands and lead times. In this subsection, the specific (<sup>s;</sup> <sup>Q</sup>)-policy is introduced along with its characteristic features such as the replenishment cycles, backorders, and mean stock level. Note that the model presented here assumes that stock-outs happen rarely and thus are negligible for calculation of the stock level; this assumption is common in the literature [22] and is also reasonable for our application as discussed later.

## 1. <sup>s;</sup> <sup>Q</sup> -Policy

All the facilities considered in the model are assumed to follow a continuous <sup>s;</sup> <sup>Q</sup> -type inventory policy. This particular policy is <sup> </sup>chosen because it enables optimization of the order quantity <sup>Q</sup>, unlike other policies such as $( R , S )$ and <sup>s;</sup> <sup>S</sup> policies, so that we can <sup>   </sup>maximize the batch launch discount. In the $( s , Q )$ inventory policy, <sup> </sup>each facility (e.g., warehouse, retailer) holds an inventory of the spare stock, and when a stock level drops to or below <sup>s</sup> available units, an order of batch size <sup>Q</sup> is placed to its attached supplier. The parameters <sup>s</sup> and <sup>Q</sup> can be optimized. The model presented in this paper focuses on the study of replenishment cycles, each of which contains a replenishment of <sup>Q</sup> units. Figure 2 illustrates replenishment cycles from a stock point of view.

## 2. Backorder

The model takes the situation of backorders into consideration in order to evaluate the efficiency of the policy. When a demand cannot be met by on-stock spare units, it is backordered. The next spares supply has to satisfy this backordered demand first upon arrival. It is important to be able to evaluate the short units (i.e., backorders) that the different facilities would be facing over replenishment cycles and have the means to control them. Knowing that the replenishment phase starts when the stock level drops to or below <sup>s</sup>, the expected backorders per cycle <sup>ES</sup> for a lead time τ become the demand exceeding <sup>s</sup> units during the time τ, which can be derived from the probability distribution of failures in Eq. (5) [22,24].

$$
E S = \sum_ {k \geq s + 1} (k - s) P _ {\tau} (D = k)\tag{5}
$$

where $P _ { \tau } ( D = k )$ is the probability of having <sup>k</sup> units of demand <sup>  </sup>during a lead time τ.

To manage the number of backorders that a facility would face, we introduce the notion of order fill rate $\rho ,$ which is the percentage of demand that is satisfied from the available stock during a cycle. The order fill rate can be found using Eq. (6).

![](../../images/images_Jakob_2018_Optimal_Spare_Strategy/a34eea61f6696b091b29171037f57f78890cad1c5e5c8c2b66759fe0820a78e2.jpg)  
Fig. 2 Representation of replenishment cycles.

![](../../images/images_Jakob_2018_Optimal_Spare_Strategy/64a031176ceab752928fb492f2d5354ffeecc1ae235731c262d1fea88f3bbb79.jpg)  
Fig. 3 Illustration of the stock level.

$$
\rho = 1 - \frac {E S}{Q}\tag{6}
$$

The order fill rate is linked to the performance of the replenishment policy at a facility. The optimal design is chosen so that the global multi-echelon spare system meets performance requirements.

## 3. Mean Stock Level

It is of particular interest to know the mean stock level at each facility to be able to further derive holding costs. From Fig. 3, the stock level takes a value between $( Q + s - N _ { \mathrm { f a i l } } ( \tau ) )$ and $( s - N _ { \mathrm { f a i l } } ( \tau ) )$ , where $N _ { \mathrm { f a i l } } ( \tau )$ <sup>   </sup>is the number of failures during a lead <sup>    </sup>time τ. Thus, assuming a linear continuous stock level drop, the mean stock level would be $( ( Q / 2 ) + s - N _ { \mathrm { f a i l } } ( \tau ) )$ . Furthermore, the <sup></sup>continuity correction factor of $1 / 2$ <sup> </sup>needs to be added to adjust the difference between the real discretized stock level drops and the assumed linear continuous stock level drops.<sup>††</sup> Equation (7) gives the resulting average stock level [28]:

$$
\overline {{S L}} = \frac {Q}{2} + s - N _ {\mathrm{fail}} (\tau) + \frac {1}{2}\tag{7}
$$

## IV. Model Formulation

## A. Overview of the Model

The aim of the model is to provide a replenishment strategy for the spare parts of a satellite constellation and establish a criterion to evaluate maintenance strategy performances. As presented by Cornara et al. [16], different spare strategies exist to ensure the maintenance of the constellation (see Table 1). To provide more flexibility in the design of the spare strategy for satellite constellations, this paper introduces a mixed strategy with multiple levels of spares, taking advantage of each approach. A visual representation of the strategy is given in Fig. 4.

The first level of spares is the constellation’s in-plane spares. The paper does not distinguish between active (overpopulation strategy) or inactive (in-plane strategy) spares and lets this choice to the reader. When a satellite failure occurs in one of the constellation orbits, and if a spare part is in stock in that orbital plane, the failed satellite is replaced using available in-plane spares. This first level allows the constellation to avoid outages with little to no time delay to replace a failed satellite.

The second level of spares is parking spares. It consists of spare satellites placed in a lower altitude orbit and at the same inclination as the constellation orbits, and these parking spare satellites are available to transfer to the in-plane spare stocks using orbital maneuvers. Note that there can be one or multiple parking orbits (i.e., multiple orbital planes); all parking orbits are circular, share the same altitude and inclination, and have their RAANs equally spaced. When the spare stock level of the in-plane locations reaches a critical level, it places an order to the parking orbits to be resupplied with spare satellites. Having this second level of spares available provides the orbital planes with the possibility to replenish their spare stocks within a relatively short amount of time (see Table 1), and can thus reduce the number of spares needed in each constellation orbit. In addition, because the parking orbits can replenish the spare stocks of any constellation orbit, they increase the flexibility of the supply chain.

Table 1 Different possible spare strategies and their approximate replacement time proposed by Ref. [16]

<table><tr><td>Strategy</td><td>Replacement time</td></tr><tr><td>Overpopulation</td><td>No time delay for replacement</td></tr><tr><td>In-plane spares</td><td>1–2 days</td></tr><tr><td>Parking spares</td><td>1–2 months</td></tr><tr><td>Ground</td><td>A few months to 1 year</td></tr></table>

Finally, the last level of spares is ground spares, that is, spare satellites on the Earth’s ground, which are considered to be always available to replenish the parking orbits thanks to the fast manufacturing assembly line that is achievable nowadays for satellite constellations [11]. Whenever a parking orbit reaches its critical stock level, it places an order to the ground spare stock to schedule a rocket launch to replenish its stock.

All levels of spare locations together are considered as a multi echelon inventory system, with stochastic demands associated with satellite failures, and stochastic lead times for both types of replenishment (from the ground to the parking orbits, and from the parking orbits to the constellation orbits). Figure 5 captures the interactions between the different levels of inventory.

The remainder of this section is organized as follows. Section IV.B introduces the general assumptions used in our model. Sections IV.C and IV.D are symmetric, as they introduce the inventories of in-plane spares and parking spares, respectively. Finally, Sec. IV.E describes the cost model used to evaluate the spare strategy, which will be used for the optimization in Sec. VI.

## B. Model Assumptions

The following presents a summary of the general assumptions of our model. Other assumptions are discussed as the model is introduced in more detail.

![](../../images/images_Jakob_2018_Optimal_Spare_Strategy/4bea8af1c9faa65a92cfe510ca5bc4b42dfd10b95dfb79eeaee3945c09ad0b96.jpg)  
Fig. 4 Overview of the multilevel spare strategy for a satellite constellation.

![](../../images/images_Jakob_2018_Optimal_Spare_Strategy/a506e0ee80080e16472ee8df13a657f921ea8b1c201a1c330d1ea7b336c20ae0.jpg)  
Fig. 5 Proposed multi-echelon inventory model for a satellite constellation.

1) Spare parts located in the first echelon (in-plane spares) are considered to be immediately available to replace a failed satellite unit. This postulate is true in the case of an overpopulated strategy; however, in case of spare satellites located in a slightly different plane to avoid collisions, the process of replacement can take up to 2 days. This delay is not considered in the model.

2) The constellation’s in-plane spare stocks get supplies from the closest (i.e., defined as the minimum waiting time) available parking orbit’s spare stock. To allow flexibility in the spare replacement flow, we allow any parking orbit to potentially resupply any orbital plane’s stocks. When a constellation orbit’s in-plane stock reaches the re order point (<sup>s</sup>-level), an order is placed to all parking orbits jointly and the spares batch is supplied from the closest parking orbit with spare availability at the time of the order.

3) Supply from the ground can be delivered only to a unique parking orbit. Indeed, as stated by Lang and Adams [13], using a single rocket launch to supply different orbital planes can turn out to be very inefficient.

4) To facilitate the tracking of the orders, an order is allowed to be processed only when no previous order is already in transit.

5) Stock-outs are assumed to happen rarely and thus are negligible for calculation of the stock levels. This assumption is reasonable fo our optimal spare strategies.

6) As the spares have to be transferred by batches both from the Earth’s ground to the parking orbits and from the parking orbits to the constellation orbits, the order quantity and re-order point at the parking orbits are assumed to be multiples of the batch size $Q _ { \mathrm { p l a n e } }$ of in-plane spares:

$$
\left\{ \begin{array}{l} Q _ {\text { parking }} = k _ {Q, \text { parking }} Q _ {\text { plane }} \\ s _ {\text { parking }} = k _ {s, \text { parking }} Q _ {\text { plane }} \end{array} \right.\tag{8}
$$

## C. In-Plane Spares Inventory Model

This subsection presents the inventory model at the in-plane spares level. It includes the demand model for in-plane spares, their resupply lead time, their backorders, and finally their mean stock level over a replenishment cycle.

## 1. Demand Model for In-Plane Spares: The Satellite Failures

Satellite reliability is the factor at stake when designing a constellation maintenance strategy, as it is responsible for failures. In our approach, satellite failures are modeled by a Poisson distribution with the satellite failure rate as its parameter, meaning the number of failures per unit time [29]. The failure rate per constellation orbital plane is deduced from the satellite failure rate:

$$
\lambda_ {\mathrm{plane}} = \frac {N _ {\mathrm{sats}} \lambda_ {\mathrm{sat}}}{N _ {\mathrm{days}}}\tag{9}
$$

Note that an underlying assumption here is that the failed satellites are replaced by new spares immediately, which would be reasonable to assume for our optimal spare strategy.

## 2. Resupply Lead Time from the Parking Orbits to the Constellation Orbits

As explained previously, the constellation’s in-plane spare stocks get supplies from the closest available parking orbit at the time of the order, as the parking orbits drift relative to the constellation orbits. The lead time from the order processing by a constellation orbit to the actual delivery is therefore stochastic and its probabilistic distribution has to be derived. First, we need to determine the probability of a parking orbit to be available, and then derive the probability of a constellation orbit to get a supply from a specific parking orbit. Furthermore, the lead time distribution is derived from the geometry of the problem and orbital mechanics considerations.

a. Probability of parking orbit availability. The probability of parking orbit availability can be derived using a binomial-like distribution. The constellation orbits need to get a supply from the closest (i.e., minimum wait time) available parking orbit, while each parking orbi can either have available spare batches or be out-of-stock. Thus, given the probability of each parking orbit being available, $P _ { \mathrm { a v } } .$ , we can derive the probability that a constellation orbit gets a supply from the <sup>i</sup>th closest parking orbit. Note that, in our application, the probability that all parking orbits are out-of-stock at the time of delivery is very small and thus can be neglected; therefore we assume that there is always one parking orbit available, which is no necessarily the closest one, to supply the in-plane stocks.

The probability that a parking orbit has available spare batches, $P _ { \mathrm { a v } } ,$ corresponds to the probability of visiting a parking orbit and no observing a stock-out. This probability is equal to the fraction of the demand not being backordered because the demand arrives at a constant rate. Therefore, $P _ { \mathrm { a v } }$ can be expressed as follows:

$$
P _ {\mathrm{av}} = 1 - \frac {E S _ {\mathrm{parking}}}{k _ {Q , \mathrm{parking}}}\tag{10}
$$

where $E S _ { \mathrm { p a r k i n g } }$ is the expected number of backorders over a replenishment cycle at a parking orbit, which is derived in Sec. IV.D.3. Note that because all of the parking orbits are analogous and evenly distributed, they are supposed to have the same $P _ { \mathrm { a v } } .$

Using this $P _ { \mathrm { a v } } ,$ , the probability of getting supply from the <sup>i</sup>th closest parking orbit is then obtained by summing all the possible cases:

$$
P (i ^ {\text {th}}) = \sum_ {k = 1} ^ {N _ {\text {parking}} - i + 1} \binom {N _ {\text {parking}} - i} {k - 1} P _ {\text {av}} ^ {k} (1 - P _ {\text {av}}) ^ {N _ {\text {parking}} - k}\tag{11}
$$

To demonstrate this expression, we consider a simple example. Assume that the chosen configuration is $N _ { \mathrm { p a r k i n g } } = 3$ and we want to <sup></sup>determine the probability of getting supply from each parking orbit.

a) 1st closest orbit: The possible cases and their respective probabilities are:

1) All orbits are available: $P = P _ { \mathrm { a v } } ^ { 3 }$

<sup></sup>2) The 1st closest orbit is available, the 2nd is available, and the 3rd is not available: $P = P _ { \mathrm { a v } } ^ { 2 } ( 1 - P _ { \mathrm { a v } } )$

<sup>  </sup>3) The 1st closest orbit is available, the 2nd is not available, and the 3rd is available: $P = P _ { \mathrm { a v } } ^ { 2 } ( 1 - P _ { \mathrm { a v } } )$

<sup>  </sup>4) The 1st closest orbit is available, the 2nd and 3rd orbits are not available: $P = P _ { \mathrm { a v } } ( 1 - P _ { \mathrm { a v } } ) ^ { 2 }$ So

$$
\begin{array}{c} P (1 \mathrm{st}) = P _ {\mathrm{av}} ^ {3} + 2 (P _ {\mathrm{av}} ^ {2} (1 - P _ {\mathrm{av}})) + P _ {\mathrm{av}} (1 - P _ {\mathrm{av}}) ^ {2} \\ = \sum_ {k = 1} ^ {3} \binom {3 - 1} {k - 1} P _ {\mathrm{av}} ^ {k} (1 - P _ {\mathrm{av}}) ^ {3 - k} \end{array}
$$

b) 2nd closest orbit: The possible cases and their respective probabilities are:

1) The 1st closest orbit is not available, the 2nd is available, and the 3rd is available: $P = P _ { \mathrm { a v } } ^ { 2 } ( 1 - P _ { \mathrm { a v } } )$

<sup>  </sup>2) The 1st closest orbit is not available, the 2nd is available, and the 3rd is not available: $P = P _ { \mathrm { a v } } ( 1 - P _ { \mathrm { a v } } ) ^ { 2 }$ So

$$
\begin{array}{c} P (2 \mathrm{nd}) = P _ {\mathrm{av}} ^ {2} (1 - P _ {\mathrm{av}}) + P _ {\mathrm{av}} (1 - P _ {\mathrm{av}}) ^ {2} \\ = \sum_ {k = 1} ^ {2} \binom {3 - 2} {k - 1} P _ {\mathrm{av}} ^ {k} (1 - P _ {\mathrm{av}}) ^ {3 - k} \end{array}
$$

c) 3rd closest orbit: The only possible case and its probability are: 1) The 1st and 2nd closest orbits are not available and the 3rd is available: $P = P _ { \mathrm { a v } } ( 1 - P _ { \mathrm { a v } } ) ^ { 2 }$ So

$$
P (3 \mathrm{rd}) = P _ {\mathrm{av}} (1 - P _ {\mathrm{av}}) ^ {2} = \sum_ {k = 1} ^ {1} \binom {3 - 3} {k - 1} P _ {\mathrm{av}} ^ {k} (1 - P _ {\mathrm{av}}) ^ {3 - k}
$$

b. Lead time distribution. The spare model presented in this paper takes advantage of the RAAN drift caused by Earth’s gravitational field (see Sec. III.A.1). Over time, a parking orbit will visit all the constellation orbits and hence is able to service failures in all of them. When a parking orbit and the constellation orbit of interest are aligned, the orbital maneuver becomes feasible and a transfer is performed (see Sec. III.A.2 for details about the transfer). The lead time to transfer batches of satellites from the parking orbits to the constellation orbits is the result of the drift time to align the orbita planes and the actual time of flight [15].

A probability distribution now has to be defined to describe the transfer time, meaning the lead time from the parking orbits to the constellation orbits. Spares are transferred from the closest parking orbit with available supply at the time of the order. As the parking orbits are angularly equally distributed, it divides the possible RAAN differences for drift into $N _ { \mathrm { p a r k i n g } }$ intervals: $[ 0 , 2 \bar { \pi } / N _ { \mathrm { p a r k i n g } } ] , [ 2 \pi /$ $N _ { \mathrm { p a r k i n g } } , 4 \pi / N _ { \mathrm { p a r k i n g } } ] , \ \dots , [ 2 \bar { \pi } ( N _ { \mathrm { p a r k i n g } } ^ { \sim } - 1 ) / N _ { \mathrm { p a r k i n g } } ^ { \sim } , 2 \pi ] .$ <sup> </sup>. Indeed, if <sup>    </sup>spares are transferred from the closest parking orbit to the constellation orbit of interest, the possible RAAN differences (ΔΩ) belong to $[ 0 , 2 \pi / N _ { \mathrm { p a r k i n g } } ] .$ , whereas if the spares are transferred from <sup></sup>the <sup>i</sup>th closest parking, $\tilde { \Delta } \Omega \in [ ( i - 1 ) ( 2 \pi \hat { / } N _ { \mathrm { p a r k i n g } } ) , i ( 2 \pi / N _ { \mathrm { p a r k i n g } } ) ]$ <sup>    </sup>Given that the drift rates are fixed by the semi-major axis and the inclination and that the parking orbits are equally distributed, we can consider that transfer times are uniformly distributed in each possible interval [see Eq. (12)].

$$
\begin{array}{l} T _ {\text { plane }} (i ^ {\text { th }}) \sim \mathcal {U} \left\{t _ {\text { transfer }} \left(\Delta \Omega = (i - 1) \frac {2 \pi}{N _ {\text { parking }}}\right), \right. \\ t _ {\text { transfer }} \left(\Delta \Omega = i \frac {2 \pi}{N _ {\text { parking }}}\right) \Bigg \} \end{array}\tag{12}
$$

where $t _ { \mathrm { t r a n s f e r } } ( \Delta \Omega )$ is the summation of the drift waiting time <sup> </sup>for an angular difference of ΔΩ and the time of flight, each of which can be calculated using Eqs. (1) and (4), respectively. With $P ( i ^ { \mathrm { t h } } )$ found in Eq. (11) and $\bar { T } _ { \mathrm { p l a n e } } ( i ^ { \mathrm { t h } } )$ <sup> </sup>found in Eq. (12), we can find the <sup> </sup>lead time distribution from the parking orbits to the constellation orbits.

## 3. Backorders at the Constellation Orbits

For the in-plane spare stocks, the expected number of backorders over a cycle, $E S _ { \mathrm { p l a n e } } .$ , can be calculated from the distribution of lead time and the expected demand during this lead time [22].

$$
E S _ {\text { plane }} = \int_ {T _ {\text { plane }}} E S _ {T _ {\text { plane }}} (s _ {\text { plane }}) f _ {\text { plane }} (T _ {\text { plane }})   \mathrm{d} T _ {\text { plane }}\tag{13}
$$

where $E S _ { \tau } ( s _ { \mathrm { p l a n e } } )$ is the expected backorders for the lead time being τ <sup> </sup>and the threshold stock level being $s _ { \mathrm { p l a n e } } , \mathrm { a n d } f _ { \mathrm { p l a n e } }$ is the probability density function of the lead time to the constellation orbits found in Sec. IV.C.2. Since an $( s , Q )$ policy is considered, the expected <sup> </sup>backorders can be found using the approach in Sec. III.B.2. With this $E S _ { \mathrm { p l a n e } } .$ , we can find the order fill rate using Eq. (14).

$$
\rho_ {\mathrm{plane}} = 1 - \frac {E S _ {\mathrm{plane}}}{Q _ {\mathrm{plane}}}\tag{14}
$$

## 4. Mean Stock Level of In-Plane Spares

Finally, the mean stock level of spare parts should be evaluated to further calculate the holding cost of the spare strategy. The resulting mean stock level of in-plane spares over a cycle is calculated as the expected mean stock level over all possible lead times. According to the theory in Sec. III.B.3, this mean stock level is given by Eq. (15).

$$
\begin{array}{l} \overline {{S L _ {\text { plane }}}} = \int_ {T _ {\text { plane }}} \left\{\frac {Q _ {\text { plane }}}{2} + s _ {\text { plane }} - N _ {\text { fail,plane }} (T _ {\text { plane }}) + \frac {1}{2} \right\} \\ \times f _ {\text { plane }} (T _ {\text { plane }})   \mathrm{d} T _ {\text { plane }} \end{array}\tag{15}
$$

Note that even though the cycle length is stochastic, this mean stock level over a given cycle is equal to the mean stock level over the entire time horizon because the cycle length distribution (governed by the demand rate) is independent of the lead time distribution. Also, an underlying assumption is that the backorders are negligible, which is a reasonable assumption for our optimal spare strategy.

## D. Parking Spares Inventory Model

The inventory model at the parking orbits also follows an $( s , Q )$ <sup> </sup>policy. This subsection presents the inventory model at the parking spares level. It includes the demand model for parking spares, thei resupply lead time, their backorders, and finally their mean stock level.

## 1. Demand Model for Parking Spares

The demand process at the spare parking orbits is derived from the failure process and policy model at the constellation orbits. Looking at the ordering process from one constellation orbital plane, an orde is placed every $Q _ { \mathrm { p l a n e } }$ failures on average and those failures are Poisson distributed. Therefore, the times between consecutive orders from this plane are Erlang- $Q _ { \mathrm { p l a n e } }$ distributed according to the relationship between the two stochastic distributions [22]. The orders placed at all spare parking orbits combined are the superposition of the orders from all constellation orbits. When $N _ { \mathrm { p l a n e } }$ is sufficiently large (meaning $N _ { \mathrm { p l a n e } } \geq 2 0 )$ ), the superposition of those $N _ { \mathrm { p l a n e } }$

Poisson processes can also be considered as a Poisson process, with rate $N _ { \mathrm { p l a n e } } ( \lambda _ { \mathrm { p l a n e } } / Q _ { \mathrm { p l a n e } } )$ [30,31]. Considering the symmetry of the <sup> </sup>problem where all spare parking orbits are equally distributed, each parking orbit is thus subject to a Poisson demand with rate $\lambda _ { \mathrm { p a r k i n g } } ,$ derived in Eq. (16).

$$
\lambda_ {\text { parking }} = N _ {\text { plane }} \frac {\lambda_ {\text { plane }}}{Q _ {\text { plane }}} \frac {1}{N _ {\text { parking }}}\tag{16}
$$

## 2. Resupply Lead Time from the Ground to the Parking Orbits

The spare parking orbits are replenished from the ground using rocket launches, with a certain lead time denoted as $T _ { \mathrm { p a r k i n g } }$ . This lead time takes into account the launch order processing time and the waiting time for the next launch window. The model proposed in this paper does not include any manufacturing delay, assuming the spare stock on the ground to be always available. The order processing time is considered to be constant, whereas the waiting time for the next launch window is assumed to be exponentially distributed in accordance with launch schedules databases (see Appendix A).

$$
T _ {\text { parking }} \sim \mathcal {E} (\mu_ {\text { launch }}) + T _ {\text { processing }}\tag{17}
$$

where $\mathcal { E } ( \mu _ { \mathrm { l a u n c h } } )$ is the exponential distribution with mean $\mu _ { \mathrm { l a u n c h } }$

## 3. Backorders at the Parking Orbits

The inventory policy for the parking spare stocks is similar to the one used for the in-plane spare stocks. Therefore, the expected number of backorders over a replenishment cycle at a parking orbit in units of batches $Q _ { \mathrm { p l a n e } }$ can be derived using the same technique as used in Sec. $\mathrm { I V } . { \cal C } . \dot { 3 } .$ , and is given by Eq. (18):

$$
E S _ {\text { parking }} = \int_ {T _ {\text { parking }}} E S _ {T _ {\text { parking }}} (k _ {s, \text { parking }}) f _ {\text { parking }} (T _ {\text { parking }}) \mathrm{d} T _ {\text { parking }}\tag{18}
$$

With this $E S _ { \mathrm { p a r k i n g } } ,$ we can find the order fill rate using Eq. (19).

$$
\rho_ {\mathrm{parking}} = 1 - \frac {E S _ {\mathrm{parking}}}{k _ {Q , \mathrm{parking}}}\tag{19}
$$

## 4. Mean Stock Level of Parking Spares

The replenishment cycles at the parking orbits follow the same characteristics as the in-plane spares cycles. Therefore, the mean stock level at the parking orbits is, in units of batches $Q _ { \mathrm { p l a n e } } .$

$$
\begin{array}{l} \overline {{{S L _ {\text {parking}}}}} = \int_ {T _ {\text {parking}}} \left\{\frac {k _ {Q , \text {parking}}}{2} + k _ {s, \text {parking}} - N _ {\text {fail}, \text {parking}} (T _ {\text {parking}}) + \frac {1}{2} \right\} \\ \times f _ {\text {parking}} (T _ {\text {parking}}) \mathrm{d} T _ {\text {parking}} \end{array} \tag {20}\tag{20}
$$

where $N _ { \mathrm { f a i l , p a r k i n g } } ( T _ { \mathrm { p a r k i n g } } )$ is the failure demand at the parking orbits <sup></sup>over the lead time $\bar { T } _ { \mathrm { p a r k i n g } }$ <sup></sup>, in units of batches $Q _ { \mathrm { p l a n e } }$

## E. Total Cost Model

The goal of the model is to estimate the cost of the spare strategy to maintain the system. For this purpose, four types of costs are considered: the manufacturing (<sup>c</sup><sub>manufacturing</sub>), holding $( c _ { \mathrm { h o l d i n g } } ) _ { : }$ launching $( c _ { \mathrm { l a u n c h } } )$ , and orbital maneuvering (<sup>c</sup> ) costs. The sum of the aforementioned cost items gives us the total expected spare strategy annual cost (TESSAC):

$$
T E S S A C = c _ {\text { manufacturing }} + c _ {\text { holding }} + c _ {\text { launch }} + c _ {\text { maneuvering }}\tag{21}
$$

## 1. Manufacturing Cost

The annual manufacturing cost is derived from the total number of failures observed over a year. As the failures are Poisson distributed with a rate $\lambda _ { \mathrm { p l a n e } }$ for each of the $N _ { \mathrm { p l a n e } }$ planes, $c _ { \mathrm { m a n u f a c t u r i n g } }$ is given by:

$$
c _ {\text { manufacturing }} = p _ {\text { sat }} \lambda_ {\text { plane }} N _ {\text { plane }} N _ {\text { days }}\tag{22}
$$

where $\lambda _ { \mathrm { p l a n e } }$ is derived in Eq. (9).

## 2. Holding Cost

The annual holding cost is associated with the spare strategy. Having spare satellites in orbits represents a substantial cost due to their operations and station keeping. The annual holding cost of in space and parking spare satellites is defined using the mean spare stock level at each orbit

$$
c _ {\text { holding }} = p _ {\text { holding }} \{\overline {{S L _ {\text { plane }}}} N _ {\text { plane }} + \overline {{S L _ {\text { parking }}}} Q _ {\text { plane }} N _ {\text { parking }} \}\tag{23}
$$

where $\overline { { S L _ { \mathrm { { p l a n e } } } } }$ and $\overline { { S L _ { \mathrm { p a r k i n g } } } }$ are given by Eqs. (15) and (20), respectively.

## 3. Launch Cost

The annual launch cost is derived from the demand generated at the parking orbits:

$$
c _ {\text { launch }} = p _ {\text { launch }} \frac {\lambda_ {\text { parking }} Q _ {\text { plane }}}{Q _ {\text { parking }}} N _ {\text { parking }} N _ {\text { days }}\tag{24}
$$

where $Q _ { \mathrm { p a r k i n g } }$ is given by Eq. $( 8 ) , \lambda _ { \mathrm { p a r k i n g } }$ is given by Eq. (16), and $p _ { \mathrm { l a u n c h } }$ is the launch cost given by Eq. (25). Two possibilities are offered regarding the launch of spare satellites, mimicking the launch options considered by OneWeb [12]:

1) Using a full capacity rocket, allowing launches up to the rocke capacity, $\dot { U } _ { \mathrm { l a u n c h } }$ satellites, at once for a fixed cost $p _ { \mathrm { l a u n c h , f u l l } }$ , which does not depend on the actual batch number of satellites effectively launched from this rocket.

2) Using a unit-satellite launcher at a cost of $p _ { \mathrm { l a u n c h , u n i t } }$ per launch, that is, per spare satellite launched. Given the specificity of this type of launcher, which is not dependent on government-maintained launch ranges to launch, it is considered possible to launch severa rockets at the same time [32]. This option requires as many launchers as the number of satellites that need to be launched.

$$
p _ {\text { launch }} = \min \left\{p _ {\text { launch,full }}, Q _ {\text { parking }} p _ {\text { launch,unit }} \right\}\tag{25}
$$

## 4. Maneuvering Cost

The annual maneuvering cost corresponds to the fuel mass required to perform maneuvers for all orbital transfers required over a year, affected by a conversion coefficient ϵ million US\$∕kg .

$$
c _ {\text { maneuvering }} = m _ {\text { fuel }} \lambda_ {\text { plane }} N _ {\text { plane }} N _ {\text { days }} \epsilon_ {\text { maneuvering }}\tag{26}
$$

where $m _ { \mathrm { f u e l } }$ is calculated in Eq. (2) and $\lambda _ { \mathrm { p l a n e } }$ is given by Eq. (9).

## V. Assessment of Model Accuracy

The model presented in the previous section is an analytical mode that allows computationally efficient evaluation of a spare policy, even for mega-scale constellations. Nevertheless, it relies on a number of simplifying assumptions (e.g., demand distribution at the parking orbits, low probability of backorders), and its accuracy needs to be assessed using simulations. Those simulations are performed with a variety of values for parameters and variables. Once the accuracy of the model is shown to be acceptable, it can be used for optimization of the spare policy without relying any more on costly simulations.

A set of 25 unique test problems is constructed using Latin Hypercube Sampling (LHS). This method generates near-random sets of parameters from a multidimensional trade space, forcing the samples to represent the real variability of the parameters [33]. The parameters used in all the simulation experiments are given in

Table 2 Fixed simulation parameters

<table><tr><td>Parameter</td><td>Notation</td><td>Value</td><td>Unit</td></tr><tr><td>Fuel mass conversion coefficient</td><td> $\epsilon_{\text{maneuvering}}$ </td><td>0.001</td><td>million US$/kg</td></tr><tr><td>Annual satellite holding cost</td><td> $p_{\text{holding}}$ </td><td>0.5</td><td>million US$/satellite/year</td></tr><tr><td>Launch capacity</td><td> $U_{\text{launch}}$ </td><td>34</td><td>satellites</td></tr><tr><td>Satellite dry mass</td><td> $m_{\text{dry}}$ </td><td>150</td><td>kg</td></tr><tr><td>Satellite manufacturing cost</td><td> $p_{\text{sat}}$ </td><td>0.5</td><td>million US$/unit</td></tr><tr><td>Full rocket launch price</td><td> $p_{\text{launch,full}}$ </td><td>47.6</td><td>million US$/launch</td></tr><tr><td>Unique satellite rocket launch cost</td><td> $p_{\text{launch,unit}}$ </td><td>10</td><td>million US$/launch</td></tr><tr><td>Effective exhaust velocity</td><td> $v_{\text{ex}}$ </td><td>2.16</td><td>km/s</td></tr></table>

Table 3 Sampled trade space for LHS

<table><tr><td>Parameter</td><td>Notation</td><td>Bounds</td><td>Unit</td></tr><tr><td>Launch order processing time</td><td> $T_{\text{processing}}$ </td><td> $30 \leq T_{\text{processing}} \leq 120$ </td><td>days</td></tr><tr><td>Constellation orbit altitude</td><td> $h_{\text{plane}}$ </td><td> $1000 \leq h_{\text{plane}} \leq 2000$ </td><td>km</td></tr><tr><td>Parking orbit altitude</td><td> $h_{\text{parking}}$ </td><td> $700 \leq h_{\text{parking}} \leq 1000$ </td><td>km</td></tr><tr><td>Inclination</td><td>i</td><td> $30 \leq i \leq 70$ </td><td>deg</td></tr><tr><td>Satellite failure rate</td><td> $\lambda_{\text{sat}}$ </td><td> $0.001 \leq \lambda_{\text{sat}} \leq 0.1$ </td><td>failures/year</td></tr><tr><td>Mean time between launches</td><td> $\mu_{\text{launch}}$ </td><td> $30 \leq \mu_{\text{launch}} \leq 90$ </td><td>days</td></tr><tr><td>Number of planes in the constellation</td><td> $N_{\text{plane}}$ </td><td> $20 \leq N_{\text{plane}} \leq 40$ </td><td>planes</td></tr><tr><td>Number of parking orbits</td><td> $N_{\text{parking}}$ </td><td> $1 \leq N_{\text{parking}} \leq 20$ </td><td>planes</td></tr><tr><td>Number of operational satellites per orbital plane</td><td> $N_{\text{sats}}$ </td><td> $20 \leq N_{\text{sats}} \leq 60$ </td><td>satellites/plane</td></tr><tr><td>Order batch size for in-plane spares</td><td> $Q_{\text{plane}}$ </td><td> $1 \leq Q_{\text{plane}} \leq 10$ </td><td>satellites</td></tr><tr><td>Order batch size for parking spares</td><td> $k_{Q,\text{parking}}$ </td><td> $1 \leq k_{Q,\text{parking}} \leq 10$ </td><td> $Q_{\text{plane}}$ </td></tr></table>

Table 2. They are representative of mega-constellation figures such as OneWeb [11]. The sampled trade space can be found in Table 3. The reorder points $s _ { \mathrm { p l a n e } }$ and $k _ { s , \mathrm { p a r k i n g } }$ for simulations are determined through the analytical model for a set of requirements on the order fill rates:

$$
\rho_ {\text { plane }} ^ {N _ {\text { plane }}} \geq 0. 9 5\tag{27}
$$

$$
\rho_ {\mathrm{parking}} ^ {N _ {\mathrm{parking}}} \geq 0. 9 5\tag{28}
$$

where $\rho _ { \mathrm { p l a n e } }$ is calculated in Eq. (14) and $\rho _ { \mathrm { p a r k i n g } }$ is calculated in Eq. (19). These requirements are set because we are interested only in the highly efficient policies with few backorders, and that is also an underlying assumption for the analytical model. The results from the simulations using these <sup>s; Q</sup> policies are used to assess the accuracy <sup> </sup>of outputs from the analytical model developed in Sec. IV: the mean stock level of in-plane spares, the mean stock level of parking spares, the order fill rate of the in-plane spare stocks, the order fill rate of the parking spare stocks, and the TESSAC. Each simulation is run for 15 years and each case includes 100 simulations. Given the simulation and modeling results, relative error percentages are calculated according to:

$$
\frac {\left| \text {value} _ {\text {sim}} - \text {value} _ {\text {model}} \right|}{\text {value} _ {\text {sim}}} \times 1 0 0\tag{29}
$$

The evaluation of the model through the relative percentage errors with simulations can be found in Table 4. The results of the simulations indicate that the analytical model performs well, with relative error percentages ranging from 0.4 to 4.1% on average. The mean stock levels of in-plane spares and parking spares reveal relative errors of 1.7 and 4.1%, respectively. Those low error percentages indicate that the model accurately estimates the stocks given the lead time distributions. The order fill rates of the in-plane spare stocks and the parking spare stocks are very well estimated by the model with relative errors of 0.8 and 0.4%, respectively. The calculation of the expected backorders of replenishment cycles through demand and lead time distributions is therefore accurately performed by the analytical model. Finally, the TESSAC error is quantified, leading to a relative error of 1.6% on average. These results indicate that the developed analytical model can approximate the simulated values well without running computationally costly simulations.<sup>‡‡</sup>

Table 4 Averaged relative error percentages of the analytica model vs simulations

<table><tr><td>Output</td><td>Relative error percentage, %</td></tr><tr><td>Mean stock level of in-plane spares</td><td>1.7</td></tr><tr><td>Mean stock level of parking spares</td><td>4.1</td></tr><tr><td>Order fill rate of the in-plane spare stocks</td><td>0.8</td></tr><tr><td>Order fill rate of the parking spare stocks</td><td>0.4</td></tr><tr><td>TESSAC</td><td>1.6</td></tr></table>

## VI. Optimization Problem Formulation

With the developed model, we can develop an optimization problem formulation to find the optimal spare strategy. The spare strategy design problem can be formulated as a mixed-integer nonlinear problem comprising six variables. The objective of the optimization problem is to design a spare strategy that minimizes the TESSAC for a given operational constellation.

## A. Variables

Table 5 presents the spare strategy decision variables along with their possible ranges of values and integer constraints.

From the specific formulation of our problem, it is important to note two major implications of the parking orbit design choice:

1) The number of spare parking orbits $N _ { \mathrm { p a r k i n g } }$ determines the maximum angular difference observed between the parking orbits and the constellation orbits. Although a large number of parking orbits results in shorter transfer times, it can also lead to higher costs.

Table 5 Optimization design variables

<table><tr><td>Variable</td><td>Unit</td><td>Bounds</td><td>Constraint</td></tr><tr><td> $N_{\text{parking}}$ </td><td>— —</td><td> $1 \leq N_{\text{parking}} \leq 20$ </td><td>Integer</td></tr><tr><td> $h_{\text{parking}}$ </td><td>km</td><td> $700 \leq h_{\text{parking}} \leq 1000$ </td><td>— —</td></tr><tr><td> $Q_{\text{plane}}$ </td><td>satellites</td><td> $1 \leq Q_{\text{plane}} \leq 10$ </td><td>Integer</td></tr><tr><td> $s_{\text{plane}}$ </td><td>satellites</td><td> $1 \leq s_{\text{plane}} \leq 10$ </td><td>Integer</td></tr><tr><td> $k_{Q,\text{parking}}$ </td><td> $Q_{\text{plane}}$ </td><td> $1 \leq k_{Q,\text{parking}} \leq 10$ </td><td>Integer</td></tr><tr><td> $k_{s,\text{parking}}$ </td><td> $Q_{\text{plane}}$ </td><td> $1 \leq k_{s,\text{parking}} \leq 10$ </td><td>Integer</td></tr></table>

2) The altitude of the spare parking orbits $h _ { \mathrm { p a r k i n g } }$ determines the relative rotation of the two orbits and, consequently, the drift time required to carry out the actual transfer of spares from the parking orbits to the constellation orbits. It also, to a smaller extent, influences the time of flight of the maneuver.

## B. Objective Function

The optimization of the spare strategy is made to minimize the TESSAC, comprising the costs of manufacturing, holding, launching, and orbital maneuvering of the spare satellites over a year of maintenance:

$$
\min _ {\boldsymbol {x} = \left[ N _ {\text { parking }}, h _ {\text { parking }}, Q _ {\text { plane }}, s _ {\text { plane }}, k _ {Q, \text { parking }}, k _ {s, \text { parking }} \right]} J (\boldsymbol {x}) = T E S S A C (\boldsymbol {x})\tag{30}
$$

where <sup>TESSAC</sup> is given by Eq. (21) according to the analytica model detailed in Sec. IV.

## C. Constraints

The constraints for the optimization problem have two components.

The first component is to enforce the launch capacity constraint. Since every launch vehicle can only deliver up to $U _ { \mathrm { l a u n c h } }$ satellites, we have the following constraint:

$$
Q _ {\mathrm{parking}} \leq U _ {\mathrm{launch}}\tag{31}
$$

where $Q _ { \mathrm { p a r k i n g } }$ is a function of $k _ { Q , \mathrm { p a r k i n g } }$ and $Q _ { \mathrm { p l a n e } }$ according to Eq. (8).

The second component is to ensure the multi-echelon spare policy to meet a global requirement for efficiency $\rho _ { \mathrm { g l o b a l } } .$ . This globa efficiency can be achieved using different relative configurations between in-plane spares and parking orbit spares, thus allowing more flexibility in the design of the inventory model at different echelons. The constraints can be written as follows:

$$
\rho_ {\text { global }} \leq \rho_ {\text { plane }} ^ {N _ {\text { plane }}} \rho_ {\text { parking }} ^ {N _ {\text { parking }}}\tag{32}
$$

where $\rho _ { \mathrm { p l a n e } }$ is calculated in Eq. (14) and $\rho _ { \mathrm { p a r k i n g } }$ is calculated in Eq. (19). This constraint limits the backorders, making them negligible for the mean stock level calculation as described in Sec. III.B.

## D. Optimizer

The optimization has to be performed using a mixed-integer nonlinear solver to meet the formulation of the problem. For the purpose of this paper, the single-objective genetic algorithm (GA) embedded in Matlab is used to complete the optimization.

## VII. Numerical Example

This section shows a numerical example of satellite mega constellation spare strategy optimization. Specifically, we focus on evaluating the value of parking orbits using our proposed inventory model. The specific strategy of using parking orbits drifting and supplying the constellation orbits has been proposed in the existing literature; however, no study has been able to optimize the operational strategy of these parking orbits in a scalable and rigorous way. Thus, it is of interest to evaluate the benefits of having parking orbits in our spare strategy design. A competitive design comprising only in-plane spares replenished directly from ground rocket launches with no parking orbits is also optimized for an <sup>s;</sup> <sup>Q</sup> policy, <sup> </sup>given the same parameters and satellite configuration. Note that, for the in-plane-only strategy, the upper bound for $Q _ { \mathrm { p l a n e } }$ is specified by the launch capacity constraint because each rocket delivers only one batch to a constellation orbit. A cost comparison is established between the in-plane-only and multi-echelon strategies.

## A. Mega-Constellation Configuration and Requirement

The implementation of a study case for a LEO satellite mega constellation is described, for which an optimization using the model previously exposed is performed. Given the nominal constellation configuration and performance requirements, the optimizer derives the best set of variables $[ N _ { \mathrm { p a r k i n g } } , h _ { \mathrm { p a r k i n g } } , Q _ { \mathrm { p l a n e } } , s _ { \mathrm { p l a n e } } , k _ { \varsigma }$ <sup>Q;</sup>parking $k _ { s , \mathrm { p a r k i n g } } ]$ <sup></sup>with respect to the objective fitness function <sup>J</sup>. The used <sup></sup>parameters remain the same as in Table 2 and the chosen LEO configuration and performance requirements are:

$$
\left\{ \begin{array}{l} h _ {\text { plane }} = 1 2 0 0 \text { km } \\ i = 5 0 ^ {\circ} \\ N _ {\text { plane }} = 4 0 \text { planes } \\ N _ {\text { sats }} = 4 0 \text { satellites / plane } \\ \lambda_ {\text { sat }} = 0. 0 5 \text { failures / year } \\ \rho_ {\text { global }} = 0. 9 5 \end{array} \right.
$$

Specific parameters related to launch are:

$$
\left\{ \begin{array}{l} \mu_ {\text { launch }} = 6 6. 7 \text {   days } \\ T _ {\text { processing }} = 9 0 \text {   days } \end{array} \right.
$$

## B. Results and Analysis

The results of the optimization for both in-plane-only and multi echelon strategies are summarized in Table 6, along with a comparison of their respective TESSAC.

The chosen design for the multi-echelon spare strategy has three parking orbits at an altitude of 792.3 km with the $( s _ { \mathrm { p a r k i n g } } , Q _ { \mathrm { p a r k i n g } } ) =$ 32<sup>;</sup> 32 inventory policy, along with the $( s _ { \mathrm { p l a n e } } , Q _ { \mathrm { p l a n e } } ) \dot { = } ( \tilde { 3 } , 4 )$ <sup>      </sup>policy at each orbit’s spare stock. The associated TESSAC is $\mathsf { \bar { \mathbf { \Lambda } } } J ^ { * } ( \mathbf { \mathbf { \Lambda } } x ^ { * } ) = \mathrm { \mathbf { \Lambda } } \mathrm { U S } \$ 31 9 . 1$ million∕year. In comparison to this chosen <sup>  </sup>design, the in-plane-only strategy optimization leads to an inventory policy of $( \bar { s _ { \mathrm { p l a n e } } } , Q _ { \mathrm { p l a n e } } ) = ( \bar { 4 } , 2 0 )$ and the associated annual <sup></sup>maintenance cost is $J ^ { * } ( x _ { \mathrm { i n - p l a n e - o n l y } } ^ { * } ) = \mathrm { U S } \Phi$ 503.2 million∕year.

<sup>  </sup>The results of the performed optimization show interesting features.

First, the comparison of the multilevel mixed strategy with a single in-plane-only strategy shows the value of introducing another level of constellation spares as parking orbits and optimally designing its inventory management, reducing the TESSAC by 36.6%.

Furthermore, parking orbits allow us to take full advantage of the batch launch discount effectively, which is captured thanks to our unique optimization framework. Indeed, spare satellites can be launched in large quantities to the parking orbits as they will supply all the constellation orbits, whose demand rate is high. On the contrary, if large batches of spare satellites are launched directly to a constellation orbital plane, they will service only in-plane failures for that specific orbital plane, whose demand rate is much lower than that of the parking orbits. As a result, given a similar batch launch quantity, launching directly to the in-plane stocks (i.e., not having parking orbits) can result in higher costs primarily due to the associated holding costs.

Table 6 Optimization results and comparison between the in-plane-only and multi-echelon spare strategie

<table><tr><td>Strategy</td><td>Chromosome</td><td>Optimal solution</td><td>TESSAC (million US$/year)</td><td>Comparison</td></tr><tr><td>In-plane-only (traditional)</td><td> $[Q_{plane}, s_{plane}]$ </td><td>[20, 4]</td><td>503.2</td><td>— —</td></tr><tr><td>Multi-echelon</td><td> $[N_{parking}, h_{parking}, Q_{plane}, s_{plane}, k_{Q,parking}, k_{s,parking}]$ </td><td>[3, 792.3, 4, 3, 8, 8]</td><td>319.1</td><td>-36.6%</td></tr></table>

Related to the above point, it is also worth noting that the optimal solution prefers a parking order quantity $Q _ { \mathrm { p a r k i n g } }$ as close as possible to the launch capacity $U _ { \mathrm { l a u n c h } } .$ . In fact, this parameter is set to $U _ { \mathrm { l a u n c h } } = 3 4$ and the results return $Q _ { \mathrm { p a r k i n g } } = 3 2$ . Therefore, this $U _ { \mathrm { l a u n c h } }$ <sup> </sup>plays a very important role in the search for the lowest possible maintenance policy and verifies the need to use satellite batch launches to reduce the cost of replenishment. Note that, although in this case $Q _ { \mathrm { p a r k i n g } }$ almost matches $U _ { \mathrm { l a u n c h } }$ , this is a result of a tradeoff between the batch launch discount and the holding cost; it is expected that, when the failure rate is very low, the optimizer would prefer to have a smaller $Q _ { \mathrm { p a r k i n g } }$ to save on holding cost.

Finally, the chosen parking orbit design $( N _ { \mathrm { p a r k i n g } } , h _ { \mathrm { p a r k i n g } } )$ also proves the value of having multiple parking orbits. The results show that the preferred design has three parking orbits. Indeed, even though having multiple parking orbits increases the costs of holding spare satellites, it also reduces the lead time to the constellation orbits; thus a sweet spot based on this tradeoff is found by the optimizer. Also, the altitude of the parking orbits (792.3 km) shows the compromise chosen by the optimizer between the duration of the lead time (especially the drift time to align the parking orbits and the constellation orbits) and the maneuver cost in terms of fuel mass required to perform the transfers. This demonstrates how our optimization can provide a direct impact on the design of a satellite constellation and its parking orbits.

## C. Sensitivity Analysis

The key parameter for the analyzed constellation spare strategy optimization is the failure rate. To observe the effects of the failure rate on the optimized spare strategy solutions, a sensitivity analysis is performed for several values of failure rates. As can be derived from [34,35], failure rates can range from 0.001 to 0.9 failures per year depending on the size of the spacecraft. Satellite constellations such as OneWeb and Starlink from SpaceX would fit in the “mini-satellite” category and thus displaying a failure rate of about 0.05 failures per year after the first year.

The relative percentage of savings when using our unique multi echelon approach using parking orbits compared with a single level of in-plane spares only is analyzed with respect to the TESSAC of each strategy. Figure 6 shows the trend observed in savings with respect to different failure rates:

This sensitivity analysis shows that, for all cases, we observe cost savings when using the multi-echelon strategy as spares are better distributed and thus provide flexibility in the supply chain. In fact, spare satellites located in the multiple parking orbits are able to service all the constellation orbits, and thus launched satellites are used more efficiently. The flow of spare satellites is more fluid as they do not get stuck in a particular plane, waiting for the next failure in this specific plane only. Even though the relative percentage of savings varies with the failure rate, the multi-echelon strategy is always preferred for the cases we tested.

![](../../images/images_Jakob_2018_Optimal_Spare_Strategy/8d0ffc7b23dfb9b2e979959c54d02f05283ddc4f8a17e1991edf41b80412530f.jpg)  
Fig. 6 Sensitivity analysis of the TESSAC savings using the multi echelon strategy vs the in-plane-spares-only strategy for different failure rates.

Another interesting observation from Fig. 6 is that the largest cost saving is observed for the case with a medium failure rate $( \lambda _ { \mathrm { s a t } } = 0 . 0 1$ failures∕year), and the cases with higher or lower failure <sup></sup>rates do not show as much cost savings by having parking orbits. This result can be interpreted as follows:

1) When the failure rate is low, the spare demands are also small, and so the optimizer does not take advantage of the batch launch discount very often. Thus, the optimized multi-echelon strategy value less the option of having parking orbits (only one parking orbit is chosen for cases $\lambda _ { \mathrm { s a t } } = 0 . 0 0 1$ failures∕year). As a result, the relative <sup></sup>saving using the multi-echelon strategy is also relatively small.

2) In the case with a high failure rate, both strategies take advantage of the batch launch discount because of the large spare demands. Even if there are no parking orbits, satellites could still be launched in batches directly to the constellation orbits to satisfy the demands. This configuration provides a relatively small saving using the multi echelon strategy.

3) The largest saving is observed for medium failure rates. The multi-echelon strategy takes full advantage of the batch launch discount, whereas in-plane-only strategy does not. The benefit of having parking orbits is the largest in this case, up to approximately 43% of cost saving.

## VIII. Conclusions

This paper presented a novel model for satellite constellation spare strategies using a multi-echelon inventory approach, and proposed an optimization formulation using this model to minimize the total annual cost of the spare strategy policy. The model views the satellite constellation spare strategy as a multilevel spare supply chain system, comprising the ground (supplier), multiple parking orbits (warehouses), and multiple orbital planes (retailers), all ruled by $( s , Q )$ inventory policies and under the assumption of stochastic demand (failures) and lead times. Our inventory model is unique in that it has multiple drifting warehouses (parking orbi spare stocks), which are all capable of resupplying all the retailers (in-plane spare stocks), and the actual resupply pathway is chosen according to the availability and the lead time distribution. The measures of performance for a chosen spare strategy are derived from the analytical model, and a cost model of a strategy is developed, including manufacturing, holding, launch, and maneuvering costs. The accuracy of the proposed model is assessed using simulations. The paper additionally developed an optimization problem formulation to minimize the cost of maintenance under performance requirements, and the numerica case study demonstrated the value of having this multi-echelon mixed-strategy spare strategy for satellite mega-constellations. The importance of the batch launch discount is stressed in those results, along with the flexibility conveyed by the multiple parking orbits being able to deliver spares to all orbital planes.

This research can be further extended in multiple directions. First, using nonidentical parking orbits and nonidentical orbita planes policies could allow more flexibility in the system to provide the same required efficiency. Also, the model presented in this paper assumes that ground spares are always available to launch with a given lead time, which is a reasonable assumption given the current satellite production rates; however, the possibility of ground spares to be out-of-stock could also be incorporated for a more accurate representation of reality. Furthermore, although this paper considered a hard efficiency constraint, an alternative approach would be to include in the objective function the cost of differen efficiency outcomes so that the model itself can make the tradeoff on the optimal level of efficiency. Finally, this paper supposes a Poisson distribution of failures; however, existing satellite reliability analysis exhibited the problem of infant mortality [36] and introduced the use of “degraded states” [37]. Therefore, more realistic consideration of satellite failure could be implemented using those observations.

Time between consecutive sucessful launches normalized histogram and exponential distribution fit for Soyuz  
![](../../images/images_Jakob_2018_Optimal_Spare_Strategy/e9144707fad55bd2ca589e9c4013d511ad88c433088063671e8618c259405abe.jpg)  
Fig. A1 Exponential distribution fit for Soyouz launches based on data from [38].

## Appendix: Launch Time Distribution

Based on the launch data retrieved from [38,39], an exponential distribution fit is derived for the times between two consecutive successful launches. The example of the Soyuz rocket launches is given in Fig. A1, where the obtained exponential parameter (i.e., the average time between two successful Soyuz launches) is 66.7 days.

## Acknowledgment

This research was supported by the Advanced Technology R&D Center at Mitsubishi Electric Corporation. We appreciate Hang Woon Lee, Tiger Hou, Hao Chen, and Hai Wang for their reviews and thoughtful suggestions for improvement.

## References

[1] Ferringer, M. P., and Spencer, D. B., “Satellite Constellation Design Tradeoffs Using Multiple-Objective Evolutionary Computation,” Journal of Spacecraft and Rockets, Vol. 43, No. 6, 2006, pp. 1404–1411. doi:10.2514/1.18788

[2] Ferringer, M. P., Clifton, R. S., and Thompson, T. G., “Efficient and Accurate Evolutionary Multi-Objective Optimization Paradigms for Satellite Constellation Design,” Journal of Spacecraft and Rockets, Vol. 44, No. 3, 2007, pp. 682–691. doi:10.2514/1.26747

[3] Budianto, I. A., and Olds, J. R., “Design and Deployment of a Satellite Constellation Using Collaborative Optimization,” Journal of Spacecraft and Rockets, Vol. 41, No. 6, 2004, pp. 956–963. doi:10.2514/1.14254

[4] Bandyopadhyay, S., Foust, R., Subramanian, G. P., Chung, S.-J., and Hadaegh, F. Y., “Review of Formation Flying and Constellation Missions Using Nanosatellites,” Journal of Spacecraft and Rockets, Vol. 53, No. 3, 2016, pp. 567–578. doi:10.2514/1.A33291

[5] Airbus, “OneWeb Satellites,” http://www.airbus.com/space/ telecommunications-satellites/oneweb-satellites-connection-for people-all-over-the-globe.html [accessed 15 March 2018].

[6] Business Insider, “Elon Musk Is About to Launch the First of 11,925 Proposed SpaceX Internet Satellites––More Than All Spacecraft That Orbit Earth Today,” 2017, http://www.businessinsider.com/spacex starlink-microsat-launch-global-internet-2018-2 [accessed 16 Feb. 2018].

[7] Space News, “FCC Gets Five New Applications for Non-Geostationary Satellite Constellations,” 2017, http://spacenews.com/fcc-gets-fivenew-applications-for-non-geostationary-satellite-constellations/ [accessed 5 Feb. 2018].

[8] Diekelman, D., “Design Guidelines for Post-2000 Constellations,” Mission Design & Implementation of Satellite Constellations, Springer, Dordrecht, The Netherlands, 1998, pp. 11–21. doi:10.1007/978-94-011-5088-0

[9] NASA Space Flight, “Iridium Marks New Satellite Network, 20 Healthy Satellites and 55 More to Launch,” 2017, https://www.nasaspacefligh .com/2017/07/iridium-satellite-network-55-more/ [accessed 29 Jan. 2018].

[10] Palmerini, G. B., “Hybrid Configurations for Satellite Constellations,” Mission Design & Implementation of Satellite Constellations, Springer, Dordrecht, The Netherlands, 1998, pp. 81–89 doi:10.1007/978-94-011-5088-0\_7

[11] OneWeb, “OneWeb Satellites Breaks Ground on the World’s First State of-the-Art High-Volume Satellite Manufacturing Facility,” 2017, http:/ www.oneweb.world/press-releases/2017/oneweb-satellites-breaks ground-on-the-worlds-first-state-of-the-art-high-volume-satellite manufacturing-facility/ [accessed 25 Jan. 2018].

[12] Space Flight Now, “OneWeb Launch Deal Called Largest Commercial Rocket Buy in History,” 2015, https://spaceflightnow.com/2015/07/01 oneweb-launch-deal-called-largest-commercial-rocket-buy-in-history [accessed 29 Jan. 2018].

[13] Lang, T. J., and Adams, W. S., “A Comparison of Satellite Constellations for Continuous Global Coverage,” Mission Design & Implementation of Satellite Constellations, Springer, Dordrecht, The Netherlands, 1998, pp. 51–62. doi:10.1007/978-94-011-5088-0.5

[14] Lansard, E., and Palmade, J.-L., “Satellite Constellation Design: Searching for Global Cost-Efficiency Trade-Offs,” Mission Design & Implementation of Satellite Constellations, Springer, Dordrecht, The Netherlands, 1998, pp. 23–31 doi:10.1007/978-94-011-5088-0

[15] Palmade, J.-L., Frayssinhes, E., Martinot, V., and Lansard, E., “The SkyBridge Constellation Design,” Mission Design & Implementation of Satellite Constellations, Springer, Dordrecht, The Netherlands, 1998, pp. 133–140. doi:10.1007/978-94-011-5088-0\_12

[16] Cornara, S., Beech, T., Belló-Mora, M., and Martinez de Aragon, A., “Satellite Constellation Launch, Deployment, Replacement and End-of Life Strategies,” 13th Annual AIAA/USU Conference on Smal Satellites, AIAA/Utah State Univ. Paper SSC99-X-1, 1999.

[17] Ereau, J.-F., and Saleman, M., “Modeling and Simulation of a Satellite Constellation Based on Petri Nets,” Reliability and Maintainability Symposium, 1996 Proceedings. International Symposium on Product Quality and Integrity, Annual, IEEE Publ., Piscataway, NJ, 1996, pp. 66–72. doi:10.1109/RAMS.1996.500644

[18] Sumter, B. R., “Optimal Replacement Policies for Satellite Constellations,” Master’s Thesis, Air Force Inst. of Technol., Wright Patterson Air Force Base, OH, 2003.

[19] Kelley, C., and Dessouky, M., “Minimizing the Cost of Availability of Coverage from a Constellation of Satellites: Evaluation of Optimization Methods,” Systems Engineering, Vol. 7, No. 2, 2004, pp. 113–122. doi:10.1002/(ISSN)1520-6858

[20] Dishon, M., and Weiss, G. H., “A Communications Satellite Replenishment Policy,” Technometrics, Vol. 8, No. 3, 1966, pp. 399–409. doi:10.1080/00401706.1966.10490373

[21] Gümüs, A. T., and Güneri, A. F., “Multi-Echelon Inventory Management in Supply Chains with Uncertain Demand and Lead Times: Literature Review from an Operational Research Perspective,”

doi:10.2514/6.2003-6214

Proceedings of the Institution of Mechanical Engineers, Part B: Journal of Engineering Manufacture, Vol. 221, No. 10, 2007, pp. 1553–1570. doi:10.1243/09544054JEM889

[22] Ganeshan, R., “Managing Supply Chain Inventories: A Multiple Retailer, One Warehouse, Multiple Supplier Model,” International Journal of Production Economics, Vol. 59, No. 1, 1999, pp. 341–354. doi:10.1016/S0925-5273(98)00115-7

[23] Schwarz, L. B., “Studies in Management Sciences,” Multi-Level Production/Inventory Control Systems: Theory and Practice, Vol. 16, North-Holland Pub. Co., North-Holland, Amsterdam, 1981, pp. 163– 193.

[24] Costantino, F., Di Gravio, G., and Tronci, M., “Multi-Echelon, Multi Indenture Spare Parts Inventory Control Subject to System Availability and Budget Constraints,” Reliability Engineering & System Safety, Vol. 119, Nov. 2013, pp. 95–101. doi:10.1016/j.ress.2013.05.006

[25] Caglar, D., Li, C.-L., and Simchi-Levi, D., “Two-Echelon Spare Parts Inventory System Subject to a Service Constraint,” IIE Transactions, Vol. 36, No. 7, 2004, pp. 655–666. doi:10.1080/07408170490278265

[26] Prussing, J., and Conway, B., Orbital Mechanics, Oxford Univ. Press, 1993.

[27] Walker, J. G., “Satellite Constellations,” Journal of the British Interplanetary Society, Vol. 37, Dec. 1984, pp. 559–572.

[28] Jensen, P., and Bard, J., Operations Research Models and Methods, Wiley, 2003.

[29] Collopy, P., “Assigning Value to Reliability in Satellite Constellations,” AIAA Space 2003 Conference & Exposition, AIAA Paper 2003-6214, 2003.

[30] Çinlar, E., “Markov Renewal Theory: A Survey,” Management Science, Vol. 21, No. 7, 1975, pp. 727–752. doi:10.1287/mnsc.21.7.727

[31] Schwarz, L. B., Deuermeyer, B. L., and Badinelli, R. D., “Fill-Rate Optimization in a One-Warehouse N-Identical Retailer Distribution System,” Management Science, Vol. 31, No. 4, 1985, pp. 488–498. doi:10.1287/mnsc.31.4.488

[32] Virgin Orbit, https://virginorbit.com/ [accessed 20 Feb. 2018]

[33] Stein, M., “Large Sample Properties of Simulations Using Latin Hypercube Sampling,” Technometrics, Vol. 29, No. 2, 1987, pp. 143– 151.

doi:10.1080/00401706.1987.10488205

[34] Dubos, G. F., Castet, J.-F., and Saleh, J. H., “Statistical Reliability Analysis of Satellites by Mass Category: Does Spacecraft Size Matter?” Acta Astronautica, Vol. 67, No. 5, 2010, pp. 584–595. doi:10.1016/j.actaastro.2010.04.017

[35] Erlank, A. O., and Bridges, C. P., “A Multicellular Architecture Toward Low-Cost Satellite Reliability,” Adaptive Hardware and Systems (AHS), 2015 NASA/ESA Conference on, IEEE Publ., Piscataway, NJ, 2015, pp. 1–8. doi:10.1109/AHS.2015.7231152

[36] Castet, J.-F., and Saleh, J. H., “Satellite and Satellite Subsystem Reliability: Statistical Data Analysis and Modeling,” Reliability Engineering & System Safety, Vol. 94, No. 11, 2009, pp. 1718–1728. doi:10.1016/j.ress.2009.05.004

[37] Castet, J.-F., and Saleh, J. H., “Beyond Reliability, Multi-State Failure Analysis of Satellite Subsystems: A Statistical Approach,” Reliability Engineering & System Safety, Vol. 95, No. 4, 2010, pp. 311–322. doi:10.1016/j.ress.2009.11.001

[38] Soyuz-2, https://en.wikipedia.org/wiki/Soyuz-2#Launch\_history [ac cessed 12 June 2017].

[39] SpaceX, “Launch Manifest,” http://www.spacex.com/missions [ac cessed 6 March 2018].

Associate Editor

E. Lightsey