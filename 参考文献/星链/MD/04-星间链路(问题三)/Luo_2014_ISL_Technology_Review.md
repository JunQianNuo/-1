---
title: 星间链路技术的研究现状与发展趋势
author: 罗大成等
year: 2014
source: 知网
type: 参考文献
subject: 数学建模-星链系统
topics:
  - ISL
  - 综述
  - 拓扑分析
parser: mineru
---

doi:10． 3969 /j． issn． 1001 － 893x． 2014． 07． 028

引用格式:罗大成，刘岩，刘延飞，等． 星间链路技术的研究现状与发展趋势［J］． 电讯技术，2014，54(7):1016 －1024．［LUO Da － cheng，LIU Yan，LIUYan － fei，et al． Present Status and Development Trends of Inter － Satellite Link［J］． Telecommunication Engineering，2014，54(7):1016 － 1024．

# 星间链路技术的研究现状与发展趋势

罗大成<sup>＊＊</sup>，刘 岩，刘延飞，徐 萍，王秋妍

(第二炮兵工程大学，西安 <sup>710025</sup>)

摘 要:星间链路技术是提高全球卫星导航系统的精度和自主导航能力的一项关键技术 介绍了全球主要卫星导航系统星间链路的建设情况，综述了国内外关于星间链路的重要研究，包括星座的特性分析<sub>、</sub>星间链路的构建准则<sub>、</sub>星间链路的拓扑分析<sub>、</sub>星间链路传播信号的设计以及星间链路信号的发射和接收等，指出了目前研究的侧重点，展望了星间链路的发展趋势和未来的研究方向 相关内容可为星间链路的进一步研究提供参考

关键词:卫星导航;星间链路;拓扑;动态路由;发展综述

中图分类号:V474． 2

文献标志码:<sup>A</sup>

<sub>文章编号</sub>:1001 － 893X(2014)07 － 1016 － 09

# Present Status and Development Trends of Inter － Satellite Link

LUO Da － cheng，LIU Yan，LIU Yan － fei，XU Ping，WANG Qiu － yan (The Second Artillery Engineering University，Xi'an 710025，China)

Abstract:Inter － satellite link technology is a key technology to improve the accuracy and autonomous navigation capabilities of global satellite navigation system． In this paper，the construction of inter － satellite links in major global navigation satellite systems are described． Some important researches on the inter － satellite links are reviewed，including analysis of a constellation of features，building guidelines of inter － satellite links，topological analysis of inter － satellite links，design of signal on the inter － satellite links，and transmitting and receiving method of signal on the inter － satellite links． The focus of the present study of inter － satellite links is pointed out，the development trends and future research directions are prospected． The research of this paper provides some reference for the profound research of inter － satellite link

Key words:satellite navigation;inter － satellite link;topology;dynamic routing; development summarization

## <sup>1</sup> 引 言

随着军民用设备对卫星应用需求的日益发展以及依赖程度逐步加深，卫星导航系统已经成为了国家的一项重要战略性基础资源，在国民经济和国防建设中发挥着越来越大的作用

目前，各导航大国卫星导航系统的正常运行主要依靠地面站来维持，如果地面站存在故障或被摧毁，则卫星导航系统的精度将下降或整个系统陷入崩溃状态，由此给经济和国防带来的损失将无法估<sub>量 。 若采用星间链路</sub>( Inter － satellite Link，ISL) <sub>技</sub>术，卫星导航系统则可以在没有地面站支持的情况下，仍正常运行较长时间 因此，星间链路具有广阔的应用前景，发展卫星导航系统的星间链路技术显得尤其重要<sub>。</sub>

星间链路是由发射机 天线以及接收机等组成的连接导航卫星之间的通信链路 采用星间链路，导航星座能够在空中组网，可以不依赖地面设备实现所有网络节点的连接，将各颗卫星有机地联结为一个整体 星间链路具有作用距离远 信息交互方便等特点，可以实现星间相对测量和星间通信的功能 通过星间链路，可以缩短星历的更新周期，提高卫星导航系统的性能，也可以实现导航卫星星座的星地联合精密定轨，提高导航定位精度;通过星间链路，还可以实现测控信号的转发，完成导航星座的间接测控，有效地减少地面站的布站数量，降低系统成本和维护费用，这对不具备全球布站能力国家的卫星导航系统(如我国的 <sup>“</sup>北斗<sup>”</sup>导航系统)的建设尤为重要<sub>。</sub> 同时，星间链路的建立，使导航星座拥有更短的路由时延和更大的通信容量，并能实现真正意义上的卫星自主导航，增强系统的生存能力

可见，星间链路是提高卫星导航系统的精度及自主导航能力的一项重要的关键技术<sub>。</sub> 目前，关于星间链路的具体技术细节的研究文献较多，但对星间链路的建设情况和涉及技术的总结性文献较少<sub>。</sub>本文在目前国内外公开发表文献的基础上，介绍了全球卫星导航系统星间链路的建设情况，分析了星间链路的技术发展现状，总结了星间链路的关键技术，指出了星间链路的研究方向<sub>。</sub>

## <sup>2</sup> 星间链路的建设现状

各导航大国竞相开展星间链路的研究和相关建设工作，美国的 <sup>GPS</sup> 系统，俄罗斯的 <sup>GLONASS</sup> 系统 欧洲的 <sup>GALILEO</sup> 系统以及我国的 <sup>“</sup>北斗<sup>”</sup>二代卫星导航系统均在未来的建设设想中提到了星间链路的建设

美国正在紧锣密鼓地推进行 <sup>GPS</sup> 现代化计划截止<sup>2012</sup> 年<sup>12</sup> 月，<sup>GPS</sup> 系统已经发展了两代多个型号的卫星，<sup>GPS</sup> 星座在轨运行的卫星包括 <sup>9</sup> 颗GPS IIA 12 <sub>颗</sub> GPS IIR 7 <sub>颗</sub> GPS IIR － M <sub>以及</sub> 3 <sub>颗</sub>GPS IIF <sub>共计</sub> 31 <sub>颗卫星</sub><sup>［1］</sup> <sub>美国在</sub> GPS Block IIR的设计上，增加了星间链路 重复编程微处理器以及冗余管理等一系列新的设计，以保证系统在 <sup>180</sup> 天时间内不靠地面支持而依然能保持 <sup>URE</sup> 小于<sup>6 m</sup>的精度<sup>［2］</sup> 第三代卫星 <sup>GPS III</sup> 也正在大力开发当中 2012 年 8 月 24 日，美国对首颗 GPS III 卫星的发射预备进行了演习，通过位于宾夕法尼亚州洛克希德 · 马丁公司车间中的 <sup>GPS IIIA</sup> 和位于科罗拉多州奥罗拉市的雷神公司的下一代 <sup>GPS</sup> 现代化运行控制段(<sup>OCX</sup>)建立的通信链路，验证了卫星基本的指挥和控制功能，测试了软件和硬件的接口<sub>。</sub>GPS IIIA <sub>卫星还将在</sub> L1 <sub>频段增加与</sub> GALILEO <sub>完全</sub>兼容<sub>、</sub>并具有互操作性的 <sup>L1C</sup> 民用信号<sub>。</sub> <sup>GPS IIIA</sup>卫星还将开展 <sup>GPS</sup> 星间链路的演示与验证工作，为<sup>GPS</sup> 星间链路的建立奠定基础<sup>［3］</sup><sub>。</sub>

此外，俄罗斯正在研制的新型导航卫星 <sup>GLO-</sup>NASS －K 也将增加星间链路功能，欧洲的 GALILEO也在规划全球导航星座的星间链路体系 ［4

我国正在有条不紊地推进 <sup>“</sup>北斗<sup>”</sup>二代卫星导 航系统的建设，根据 <sup>“</sup>北斗<sup>”</sup>二代的工程规划，将在 <sup>2015</sup> 年到<sup>2020</sup> 年期间建成覆盖全球的卫星导航系 统，系统建成后的空间段包括 <sup>5</sup> 颗 <sup>GEO</sup> 卫星和 <sup>30</sup> 颗非静止轨道卫星(<sup>27 MEO</sup> 卫星 <sup>+ 3</sup> 颗 <sup>IGSO</sup> 卫 星)<sup>［5］</sup> <sub>。</sub>

<sup>2011</sup> 年 <sup>4</sup> 月，第 <sup>8</sup> 颗 <sup>“</sup>北斗<sup>”</sup>导航卫星发射成功，标志着<sup>“</sup>北斗<sup>”</sup>区域导航卫星系统建设完成 我国目前尚不具备全球性战略地理资源，<sup>“</sup>北斗<sup>”</sup>系统的运行控制段只能在国内布站，这极大地限制了对卫星的测控和维护<sub>。</sub> 因此，我国的 <sup>“</sup>北斗<sup>”</sup>系统迫切需要建设导航星座星间链路来弥补这一不足，支持导航星座依赖少量地面站甚至不依赖地面站运行为此，谭述森<sup>［6］</sup>等国内知名专家对 <sup>“</sup>北斗<sup>”</sup>卫星导航系统的发展进行了思考与论述，指出了星间链路在<sup>“</sup>北斗<sup>”</sup>卫星应用中的重要性

## <sup>3</sup> 星间链路技术研究现状

星间链路的主要任务是实现导航卫星星间相对测量和星间通信 星间链路通常由发射机子系统天线子系统 捕获和跟踪子系统以及接收机子系统等组成<sup>［7］</sup> 发射机子系统主要完成信号的编码 译码 变频和放大等工作;天线子系统主要完成星间链路上信号的收发工作;捕获和跟踪子系统主要完成天线的指向控制，确保星间链路两端的天线能互相对准;接收机子系统主要完成信号的变频 放大 检测 解调和译码以及测量误差的补偿等工作

目前，国内外诸多学者对星间链路相关技术进行了研究和探讨，取得了丰硕的成果 根据星间链路的任务需要以及组成，这些研究成果大致可以分为导航星座特性分析 星间链路构建准则 星间链路的网络拓扑分析 星间链路信号的设计 星间链路信号的发射和接收以及星间链路的性能分析等

## <sup>3．1</sup> 导航卫星星座特性分析

现有的 <sup>GLONASS</sup> 系统并不支持星间测距，<sup>“</sup>伽利略<sup>”</sup>和<sup>“</sup>北斗<sup>”</sup>仍处于开发实施阶段，诸多关键参数尚未确定或公开，因此星间链路技术的研究主要针对 <sup>GPS</sup> 卫星导航系统的 <sup>Walker</sup> 星座和编队飞行小卫星星座<sub>。</sub>

对于 <sup>Walker</sup> 星座和编队飞行小卫星星座内的卫星而言，需要建立同一轨道平面内卫星之间的星间链路和相邻轨道平面内卫星之间的星间链路 对于立体多层次的星座，还有可能需要建立不同层次轨道内卫星之间的星间链路<sub>。</sub> 那么对于一个具体的导航星座，究竟能否建立星间链路? 星间链路建立的难易程度如何? 所建立的星间链路是否能够保持? 则是导航卫星星座特性分析需要解决的问题<sub>。</sub>

针对能否建立星间链路的问题，文献［<sup>8</sup>］指出，可以采用仰角 方位角和星间距离的变化特性来描述星间链路实现的难易程度和性能 仰角和方位角表明了用于建立星际链路的天线指向的变化，星间距离则表明了星际链路的传输损耗特性 星间链路能否建立与卫星间的星间距离 方位角和仰角相关文献［9］研究了 24/3/1 构型的 Walker 星座卫星的可见性及星间链路的特性，探索了建立异轨星间链路的可行性 文献［<sup>10</sup>］研究了 <sup>24/3/2</sup> 构型的<sup>Walker</sup> 星座星间链路的构建方法和链路可见性，计算和分析了所建立星间链路的方位角 仰角和星间距离，得出了 <sup>Walker</sup> 星座可建立多条星间链路的结论 文献［11］分析了24/3/2 构型的 Walker 星座空间的结构 卫星与卫星之间的相对运动规律和星座几何构型，得到了星座星间链路的基本几何关系文献［12］分析了24/3/2 构型的 Walker 星座的卫星间可见性以及星间链路相关约束条件 文献［<sup>13</sup>对编队飞行小卫星的星间链路的方位角 仰角及星间距离等几何特性进行了分析，得出了小卫星编队构形几何特性随轨道参数变化而动态改变的规律<sub>。</sub>文献［<sup>14</sup>］对同层间激光链路 异层间激光链路俯仰角 方位角以及星间距离参数和 <sup>GEO</sup> 对 <sup>LEO</sup> 覆盖特性进行了仿真<sub>。</sub>

针对星间链路建立的难易程度如何的问题，文献［<sup>8</sup>］指出，星间链路的仰角和方位角的变化速度越快，动态范围越大，对卫星的姿态稳定性和星载天线跟踪性能的要求就越高，星间链路的建立则越难同时，星间距离越长，通过星间链路传播信号的损耗越大;在天线的指向精度和发射功率相同的情况下，星间距离越短，通过星间链路传播数据的速率越高因此，对一个具体的导航星座而言，星间链路的仰角和方位角变化越小越慢，星间距离越短，则星间链路的建立越容易

针对所建立星间链路是否能够保持的问题，由于建立了星间链路的卫星在星座运行过程中，星间链路的仰角和方位角以及星间距离是随时间变化的，为此文献［<sup>8</sup>］指出，星间链路是否能够保持，与星间链路的仰角和方位角以及星间距离随时间的变化率相关<sub>。</sub>

## <sup>3．</sup> <sup>2</sup> 星间链路构建准则

导航星座必须通过星间链路实现星座内所有卫星的直接或间接连通，这就涉及到星座资源优化分配的问题，即避免出现某颗卫星建立星间链路的条数过多或过少的问题 基于此，国内外的学者提出了基于星座资源优化配置策略的星间链路构建准则 文献［<sup>15</sup>］介绍了一种最多资源策略:星间链路在初始化或重建时，<sup>LEO</sup> 卫星与在可视范围内具有最多空闲资源的 <sup>MEO</sup> 卫星建立并维持层间星间链路，当 <sup>MEO</sup> 卫星变为不可见时，重新选择其他可视范围内具有最多空闲资源的 <sup>MEO</sup> 卫星建立层间星间链路 该策略可以保证 <sup>MEO</sup> 星座资源的均匀利用<sub>。</sub> 文献［<sup>16</sup>］提出了一种集中的资源策略:在导航星座星间链路网络拓扑重构时，每颗 <sup>LEO</sup> 卫星与可视范围内具有最多空闲资源的 <sup>MEO</sup> 卫星建立层间星间链路 该策略可以保证所有层间星间链路的下一次实际重建时间相同，是所有层间星间链路下一次理论重建时间的最小值<sub>。</sub>

在导航星座中，星间距离决定了星间链路传播信号的时延，基于此，一些学者提出了星间链路的最近距离策略及其改进策略 文献［<sup>16</sup>］介绍了一种最近距离策略:<sup>LEO</sup> 卫星始终与距离最近的 <sup>MEO</sup>卫星建立层间星间链路 <sup>LEO</sup> 卫星不断检测与可视 <sup>MEO</sup> 卫星间的距离，一旦发现有距离更近的<sup>MEO</sup> 卫星，立即拆除与当前 <sup>MEO</sup> 卫星间的层间星间链路并与距离更近的 <sup>MEO</sup> 卫星建立层间星间链路 该策略可以保证所建立的每条层间星间链路距离最小化，但将导致最频繁的层间星间链路重建文献［<sup>17</sup>］提出了一种集中的距离策略:在导航星座星间链路网络拓扑重构时，每颗 <sup>LEO</sup> 卫星独立寻找距离最近的<sup>MEO</sup> 卫星建立层间星间链路，并计算新建立的层间星间链路能够维持的时间，从而得到该层间星间链路的下一次理论重建时间 为了在相同时间进行层间星间链路重建，需将所有层间星间链路的下一次实际重建时间设置为相同的时间值 显然，为了保证所有层间星间链路不会中断，实际重建时间设置为所有层间星间链路下一次理论重建时间的最小值 基于最近距离策略的星间链路算法最典型的有最短路径算法，最短路径算法的链路时延最少，但链路切换次数较多，卫星空间作业有一定难度<sup>［17］</sup> <sub>。</sub>

星间链路还有一个重要的参数，即星间链路保持的时间<sub>。</sub> 星间链路保持的时间越长，则星间链路的切换次数越少，基于此，国内外提出了星间链路构建的最长连接时间策略及其改进策略<sub>。</sub> 文献［<sup>16</sup>介绍了一种最长连接时间策略:初始时或链路重建时，<sup>LEO</sup> 卫星选择能够为自己提供最长连接时间的<sup>MEO</sup> 卫星建立层间星间链路，并维持该链路，直到该 <sup>MEO</sup> 卫星将要飞出 <sup>LEO</sup> 卫星的可视范围，重新选择能够为自己提供最长连接时间的 <sup>MEO</sup> 卫星该策略可以保证所建立的每条层间星间链路的重建次数最小化，但层间星间链路的平均距离较长<sub>。</sub> 文献［<sup>17</sup>］提出了一种集中的时间策略:在导航星座星间链路网络拓扑重构时，每颗 <sup>LEO</sup> 卫星独立寻找能够提供最长连接时间的 <sup>MEO</sup> 卫星建立层间星间链路 所有层间星间链路的下一次实际重建时间相同，是所有层间星间链路下一次理论重建时间的最小值 基于最长连接时间的星间链路算法最典型的有 <sup>K</sup> 短路径算法 <sup>K</sup> 短路径算法链路切换次数较少，但链路时延较长，而且转发卫星有时需要转发多个信息，容易引起混乱<sub>。</sub>

综上所述，在进行链路选择时，必须综合考虑最近距离策略 最长连接时间策略和最多资源策略 <sup>3</sup>种类型的星间链路构建策略，建立性能最优的星间链路<sub>。</sub>

## <sup>3．</sup> <sup>3</sup> 星间链路的拓扑分析

星间链路的拓扑<sup>［9］</sup>是指导航星座中各卫星之间的连通关系，包括导航卫星相互之间的能见关系，星间链路的指向(仰角和方位角)及指向变化率 星间距离及距离变化率等

根据是否存在切换，星间链路可分为静态星间链路(永久性星间链路)和动态星间链路两大类，因此星间链路的拓扑分析研究也可从这两大类进行归纳和分析

## <sup>3．3．1</sup> 静态星间链路拓扑分析

构建静止星间链路，需要解决以下几个问题:一是静态星间链路建立的条件，即在导航卫星星座中，拟建立静止星间链路的两颗卫星是否始终可见? 二是静态星间链路的最优分配，即在可能建立静止星间链路的所有卫星中，链路如何最优分配? 三是静止星间链路参数的变化带来的影响 静止星间链路虽不存在链路的切换，然而链路的参数(包括星间距离 仰角和方位角)均动态变化，由此给星间链路中信号的发射功率 捕获和跟踪带来的影响如何?

针对星间链路建立条件的问题，文献［<sup>18</sup>］分析了永久性星间链路存在的条件，解决了不同轨道面以及不同轨道高度卫星之间相对移动造成的星间链路频繁切换问题 文献［<sup>19</sup>］通过对标准型 <sup>Walk-</sup><sup>er24/3/2</sup> 星座卫星的星间几何特性和空间参数的分析，设计了一种具有低跳数全网覆盖通信能力的星间固定链路拓扑结构，有效地减少了星间链路的数量，增强了系统的可实施性和可靠性

针对链路的优化分配问题，文献［<sup>20</sup>］利用图论方法来解决若干颗卫星通过星间链路组网中的链路分配及动态切换问题

针对星间链路参数变化带来的影响的问题，文献［<sup>21</sup>］指出，星间距离的大小及其变化范围对星间通信系统的功率大小和变化范围提出了基本要求，星间链路指向的变化决定了安装在卫星上的发射接收天线的复杂和困难程度，同时也与相应装置的体积和重量存在密切的关系 文献［<sup>22</sup>］指出，应该根据星间链路指向角度变化率可以指导星载天线自动跟踪功能的设计和应用，分析星间链路指向变化率特征，自动调整星载天线的跟踪准确度和跟踪速度，可使星载天线始终处于良好的接收状态

## <sup>3．</sup> <sup>3．</sup> <sup>2</sup> 动态星间链路拓扑分析

动态星间链路的最大特点就是链路是动态的，即星间链路存在切换和重构 国内外学者对于动态星间链路拓扑分析的研究，主要集中在如何构建动态星间链路以及动态星间链路如何进行切换和重构两方面上<sub>。</sub>

针对动态星间链路如何构建的问题，主要需要确保星间链路的两颗卫星能够捕获和跟踪到对方的发射信号 每条动态链路在建立前，建立链路的两颗卫星的天线都必须准确地指向对方，由于卫星的相对位置和姿态始终处于动态变化中，因此需要一个星间链路的捕获和跟踪的扫描区域，即预置不确定角 如果预置不确定角的值过小，则不能完成星间链路间信号的捕获和跟踪，即无法完成链路的建立;如果预置不确定角的值过大，星间链路信号的捕获和跟踪需要扫描过大的区域，将增大捕获时间，也导致星间链路发射功率的增加，发射信号和接收信号设备体积的增加，加大实现难度 针对预置不确定角的问题，文献［<sup>23</sup>］指出预置不确定角的因素主要有卫星的姿态精度 卫星的轨道预报精度，以及卫星轨道摄动 天线指向机构的执行精度等，其中姿态精度和轨道预报精度起决定作用<sub>。</sub>

对于动态星间链路的重构问题，国内外学者的研究主要集中在动态星间链路的重构方法和动态星间链路的路由设计两方面上<sub>。</sub>

针对星间链路的重构问题，文献［<sup>23</sup>］为解决与故障卫星节点相连的星间链路失效而导致传输延迟大幅增加的问题，提出了一种新的链路重构方法<sub>。</sub>文献［<sup>24</sup>］研究了星间链路切换对多层卫星网络拓扑结构变化的影响，给出了卫星网络运行周期的时隙划分算法<sub>。</sub>

针对星间链路路由设计问题，文献［<sup>25</sup>］介绍和分析了美国 <sup>GPS</sup> 系统星间链路设备配置和链路协议，并阐述了星间链路工作模式<sub>。</sub> 文献［<sup>26</sup>］针对具有星际链路的 <sup>LEO/MEO</sup> 卫星网络，采用时间离散化的链路状态增量更新的虚拟拓扑路由算法，降低了网络开销，提出了一种多点转发节点选举算法，提高了路由收敛速度和网络资源利用率，最终设计了一种具有自主运行能力的卫星网络动态路由协议(<sup>SDRP</sup>) 文献［<sup>24</sup>］设计了一种基于网络拓扑变化预计算和链路状态直接报告的多层卫星网络路由协议(<sup>MLSNRP</sup>)，并分析证明了该协议的可行性和高效性;在此基础上，基于有限状态机理论，建立了<sup>MLSNRP</sup> 路由协议仿真模型

事实上，要完成一个导航星座的连通性，既需要建立静态星间链路，也需要建立动态星间链路 文献［27］对 Walker24/3/2 星座的可见性进行了分析，并据此设计了一种静态拓扑结构和一种动态拓扑结构，可满足整个星座星间通信的需求，也能初步满足星座自主导航的需求

## <sup>3．4</sup> 星间链路的信号设计

卫星导航系统星间链路的频带<sup>［21］</sup>既包括国际<sub>电联分配的在</sub> UHF <sub>到</sub> EHF(190 GHz) <sub>的</sub> 14 <sub>个频</sub>段，也包括未分配的激光频段 这些频段一部分可归纳为无线电部分，另一部分可归类为光学部分因此若按频率进行划分，星间链路可分为射频链路和光学链路

射频链路主要是无线电链路，具有成本低廉 测距方式灵活 技术比较成熟等优点，但存在数据率较低 宽波束的无线电链路的抗干扰能力难以提升的缺点<sup>［4］</sup>

光学链路主要是激光链路，具有通信容量大 测量精度高 抗干扰能力强和隐蔽性好等特点，但存在造价昂贵 设备结构复杂 体积较大 功耗很高 需要扫描和对准<sub>、</sub>测量距离较短等缺点<sub>。</sub>

<sub>文献</sub>［28］<sub>介绍了</sub> GPS －2R/2R － M <sub>星间链路的</sub>电文格式<sub>。</sub> 目前 <sup>GPS －2R/2R －M</sup> 的通信频段为超高频(<sup>250 ～290 MHz</sup>)，星间链路的电文由测距帧和数据帧组成<sub>。</sub> 测距帧和数据帧均采用时分复用多址方式，即给每一颗导航卫星分配一个维持<sup>1．5 s</sup>的时隙，<sup>24</sup> 颗在轨工作的导航卫星所分配的时隙各不相同，可见测路帧和数据帧的长度均为<sup>36 s</sup><sub>。</sub> 测距帧主要在<sup>36 s</sup>时间内完成星座所有卫星的一遍轮询，完成星座卫星播发测距信号的遍历 数据帧通常位于测距帧之后，主要在<sup>36 s</sup>时间周期内完成星座卫星播发数据信号的遍历 <sup>GPS －2R/2R － M</sup> 星间链路传输的一个主帧通常由 <sup>1</sup> 个测距帧和 <sup>24</sup> 个数据帧共<sup>25</sup> 帧组成，可见一个主帧的长度为<sup>900 s</sup><sup>GPS －2R/2R －M</sup> 卫星星间链路测距周期可选择为900 s<sub>的倍数</sub>，<sub>通常为</sub>15 min <sub>、</sub> 1 h <sub>、</sub> 2 h <sub>、</sub> 3 h <sub>、</sub> 4 h<sub>和</sub>6 h等，其中<sup>1 h</sup>为缺省值设置<sub>。</sub>

文献［<sup>29</sup>］在明确星间通信特点的条件下，选择<sup>LDPC</sup> 码作为星间信道的编码方式进行研究，给出了该信道编码的构造方法和编译码方式，对其常用的译码方法进行了仿真对比，并对译码算法本身的特点进行了探讨，给出了星间信道上的性能仿真

## <sup>3．5</sup> 星间链路信号的发射和接收研究现状

## <sup>3．5．1</sup> 星间链路天线技术

星间链路信号的发射主要依靠天线子系统 对此国内外学者的研究主要集中在天线的设计 天线的指向控制 发射信号的参数设计等

文献［<sup>30</sup>］在片状四臂螺旋天线的基础上提出了一种适用于星间链路的四臂螺旋天线，验证了所设计的四臂螺旋天线的性能

文献［<sup>22</sup>］指出，星间链路指向角度变化率可以指导星载天线自动跟踪功能的设计和应用，分析星间链路指向变化率特征，自动调整星载天线的跟踪准确度和跟踪速度，可使星载天线始终处于良好的接收状态<sub>。</sub> 文献［<sup>31</sup>］分析了中继星和用户星中星间链路角跟踪系统中 <sup>Ka</sup> 天线角误差电压的交叉耦合，简述了校正方案<sub>。</sub>

文献［<sup>7</sup>］在多层卫星网络微波星间链路参数间的关系进行分析的基础上，分别在 <sup>S</sup> 频段和 <sup>Ka</sup> 频<sub>段上分析计算了</sub> GEO / IGSO<sub>、</sub> GEO /MEO <sub>和</sub> IGSO /<sup>MEO</sup> 卫星星间链路上发射信号的 $E _ { b } / N _ { 0 }$ <sub>、</sub> 发射功率 天线直径和数据速率间的关系

## <sup>3．5．2</sup> 星间链路测量技术

星间链路的测量任务是为卫星轨道和钟差估计提供测量值 导航星座的建立和自主导航的实现过程中，最受关注的即是星间链路的精密测距功能<sub>。</sub>目前精度最好 比较成熟 得到广泛应用的是卫星双单向测量方法，基本的测量是信号传播时延

目前国内外主要的远距离空间测距系统均采用伪码测距体制，如美国的 <sup>GPS －2R</sup> 卫星星间距离的测距采用的就是伪码测距体制 <sup>GPS －2R</sup> 卫星实施双频单向测距，在测距帧期间，采用测距模式，任意一颗 <sup>GPS －2R</sup> 卫星在分配的时隙里发射测距信号，其他所有可见的导航卫星进行接收，对 <sup>UHF</sup> 频段的测距信号进行处理，利用两个不同频率消除电离层效应的影响，完成伪距测量 在数据帧期间，采用数据发送模式，每颗卫星在其分配的时隙里发射与自身相关的数据参数，主要包括伪距测量的计算结果 估计出来的卫星位置和时钟参数及相应的估计方差<sub>。</sub>

对于星间链路测量技术的研究，主要集中在星间链路的预算设计<sub>、</sub>星间链路信号传播的误差分析及补偿以及星间链路的距离模型设计等方面上<sub>。</sub>

针对星间链路预算设计的问题，文献［<sup>32</sup>］对星间链路的发射功率 传输耗损等进行了分析，讨论了<sup>Walker －</sup> δ 星座的星间链路预算

针对星间链路信号的误差分析及补偿问题，文献［<sup>5</sup>］指出星间距离测量的误差来源主要有:发射<sup>/</sup>接收机噪声 设备时延误差 天线相位中心误差 电离层延时误差 多路径效应误差 相对论效应误差和动态应力误差等 文献［<sup>33</sup>］从星间距离 星间链路接收机的接收功率 星间链路传播信号的载噪比 星间链路传播信号的误码率四个方面入手，对星间链路进行了仿真分析，得出了星间链路在自由空间传播衰减的变化规律

针对星间距离模型的设计问题，文献［<sup>34</sup>］提出了一种适用于星间双向异步通信链路直传 转发模式的误码率测试方法，实现了多节点的星间通信链路数据传输误码率的检测<sub>。</sub> 文献［<sup>35</sup>］提出了一种用来精确计算星间链路的距离 <sup>“</sup>交点<sup>”</sup>模型，并在此基础上对星间链路传播信号的载噪比<sub>、</sub>多普勒频移和星间链路系统门限等参数进行了分析

## <sup>3．6</sup> 星间链路的性能分析

星间链路的性能分析主要对星间链路的构建方案 星间链路的稳定性 星间链路的测量以及星间链路的性能进行仿真验证 文献［<sup>36</sup>］讨论了 <sup>GPS</sup> 星间链路数据的模拟方法 文献［<sup>37</sup>］结合永久星间链路和非永久星间链路设计准则以及约束连通度设计准则，提出了代价函数的概念，并针对三层卫星星座，给出了该星座的星间链路设计的具体步骤 文献［12］分析了24/3/2 构型的 Walker 星座的卫星间可见性以及星间链路相关约束条件，并对最小跳数最短路径和网络流量均衡<sup>3</sup> 种不同的星间链路拓扑方案进行了仿真<sub>。</sub> 文献［<sup>36</sup>］提出了一种衡量星间链路稳定性的模型，并基于此模型给出了 <sup>LEO</sup> <sup>/</sup><sup>MEO</sup> 双层卫星网的星间链路设计方案<sub>。</sub>

## <sup>4</sup> 星间链路技术的发展和研究趋势

从国内外研究现状来看，星间链路技术的发展和研究方向主要有以下几个方面:

(<sup>1</sup>)加强星间链路研究的国际合作，采用更高 频段链路(<sup>Ka</sup><sub>、</sub><sup>V</sup> 频段等)或激光链路，采用更完善 的星上处理技术，达到更高的星间测量精度和更快 的链路数据通信速率<sup>［21］</sup>;

(<sup>2</sup>)星间链路参数的变化规律<sup>［29］</sup> 分析星间链路几何参数(仰角和方位角 星间距离等)理论计算公式及其微分公式，总结星间链路的静态及动态性能随卫星轨道等要素变化的规律(如星间链路指向的变化规律);

(<sup>3</sup>)星间链路信号传输的误差建模及补偿 分析星间通信环境，建立空间传输损耗和多普勒频移的数学模型及其随卫星轨道要素变化的规律;分析在空间状态下，星间链路的参数(仰角和方位角<sub>、</sub>星间距离等)变化以及导航卫星星体振动幅度给星间链路的比特误码率带来的影响等;

(<sup>4</sup>)星间链路最佳路由选择 主要分析在导航星座的众多卫星中，如何选取最佳的星间链路路由，并在此基础上设计得出星间链路建立过程中的最优化搜索算法;

(<sup>5</sup>)星间链路的抗毁性设计 主要研究星间链路冗余连接设计和星间链路的功能维持:链路冗余连接设计主要在网络结构以及卫星节点允许的前提下，尽量对符合条件的节点之间建立通信链路，以提高网络的性能与容量;失效链路的功能维持主要包括在卫星的可见性发生变化，或卫星出现轨道机动以及存在故障时，断开失效的卫星星间链路，启用视距范围内次相邻卫星节点，建立新的星间链路

## <sup>5</sup> 结 论

星间链路是卫星导航定位系统的重要组成部分，无论是已经成熟的 <sup>GPS</sup> 系统，还是我国正在建设的<sup>“</sup>北斗<sup>”</sup>二代卫星导航系统，星间链路都是重点建设的内容之一 针对星间链路技术的特点 建设情况 研究进展与方向，进一步深入开展星间链路技术的研究，并促进研究成果向实际应用转化，将为卫星导航系统星间链路的建设提供科学的理论依据和扎实的技术保障<sub>。</sub>

## 参考文献:

［1］ Wu A． Evaluation of GPS Block IIR Time Keeping System for Integrity Monitoring［C］/ /Proceedings of 39th Annual Precise Time and Time Interval Meeting． Long Beach， CA:IEEE，2007:351 － 362．

［2］ Rajan J A． Highlights of GPS IIR autonomous navigation ［C］/ / Proceedings of the 58th Annual Meeting of ION and CIGTF 21st Guidance Test Symposium． Albuquerque， NM:IEEE，2002:354 － 363．

［3］ 赵爽．2012 年美国 GPS 系统发展综述［J］． 卫星应用，2013(2):18 － 20．ZHAO Shuang． Review of the development of the U． S．GPS system in 2012［J］． Satellite Application，2013(2):18 － 20． (in Chinese)

［<sup>4</sup>］ 林益明，何善宝，郑晋军，等<sup>．</sup> 全球导航星座星间链路技术发展建议［J］． 航天器工程，2010，19(6):1 － 7．LIN Yi － ming，HE Shan － bao，ZHENG Jin － jun，et al．Development Recommendation of Inter － satellites Linksin GNSS ［J］． Spacecraft Engineering，2010，19(6):1 －7． (in Chinese)

［<sup>5</sup>］ 朱俊<sup>．</sup> 基于星间链路的导航卫星轨道确定及时间同步方法研究［<sup>D</sup>］<sup>．</sup> 长沙:国防科学技术大学，<sup>2011</sup>ZHU Jun． Research on Orbit Determination and Time Syn-chronizing of Navigation Satellite Based on Crosslinks［D］． Changsha:National University of Defense Technolo-gy，2011． (in Chinese)

［<sup>6</sup>］ 谭述森<sup>．</sup> 北斗导航卫星系统的发展与思考［<sup>J</sup>］<sup>．</sup> 宇航学<sub>报</sub>，2008，29(2):391 － 396．TAN Shu － sen． Development and Thought of CompassNavigation Satellite Systems［J］． Journal of Astronautics，2008，29(2):391 － 396． (in Chinese)

［<sup>7</sup>］ 田雍容，卢晓春，黄飞江<sup>．</sup>多层卫星网络星间链路性能分析与设计［J］． 时间频率学报，2010，33(2):140 －145．TIAN Yong － rong，LU Xiao － chun，HUANG Fei － jiang．Design and Performance Analysis of Inter － satellite Linkin Multilayer Satellite Network［J］． Journal of Time andFrequency，2010，33(2):140 － 145． (in Chinese)

［<sup>8</sup>］ 吴廷勇<sup>．</sup> 非静止轨道卫星星座设计和星际链路研究［D］． 成都:电子科技大学，2008．WU Ting － yong． Research on Non － Geostationary OrbitSatellite Constellation Design and Inter － Satellite Link［D］． Chengdu: University of Electronic Science and

Technology of China，2008． (in Chinese)

［<sup>9</sup>］ 何家福，姜勇，张更新，等<sup>．</sup> 一种具有异轨星间链路的<sup>Walker</sup> 星座网络拓扑与路由生成方案［<sup>J</sup>］<sup>．</sup> 解放军理工大学学报(自然科学版)，2009，10(5):409 － 413．HE Jia － fu，JIANG Yong，ZHANG Geng － xin，et al． To-pology and route production scenario of Walker satelliteconstellation network with inter － satellite link ［J］． Jour-nal of PLA University of Science and Technology(NaturalScience Edition)，2009，10(5):409 － 413． (in Chinese)

［<sup>10</sup>］ 杨霞，李建成<sup>． Walker</sup> 星座星间链路分析［<sup>J</sup>］<sup>．</sup> 大地测<sub>量与地球动力学</sub>，2012，32(2):143 － 147．YANG Xia，LI Jian － cheng． Inter － satellite Links Anal-ysis of Walker Constellation ［J］． Journal of Geodesy andGeodynamics，2012，32(2):143 － 147． (in Chinese)

［<sup>11</sup>］ 范丽，张育林<sup>． Walker</sup> 星座星间链路构建准则及优化设计研究［J］． 飞行力学，2007，25(2):93 － 96FAN Li，ZHANG Yu － lin． Construction Rules and DesignOptimization of ISLs in Walker Constellation sn［J］． FlightDynamics，2007，25(2):93 －96． (in Chinese)

［<sup>12</sup>］ 孙桦，郝晓鹏，冯文全，等<sup>．</sup> 基于最小 <sup>PDOP</sup> 准则的星间链路拓扑方案［<sup>J</sup>］<sup>．</sup> 北京航空航天大学学报，<sup>2011</sup>，37(10):1245 － 1249SUN Hua，HAO Xiao － peng，FENG Wen － quan，et al．Inter － satellite links topology scenario based on mini-mum PDOP criterion［J］． Journal of Beijing University ofAeronautics and Astronautics，2011，37 ( 10 ): 1245 －1249． (in Chinese)

［<sup>13</sup>］ 张立巍，朱立东，吴诗其<sup>．</sup> 椭圆轨道编队小卫星星间链路几何特征研究［<sup>J</sup>］<sup>．</sup> 电子与信息学报，<sup>2006</sup>，<sup>28</sup>(5):861 － 864．ZHANG Li － wei，ZHU Li － dong，WU Shi － qi． Study onthe ISL ’ s Geometrical Characteristics of Small SatellitesFormation Flying in Elliptical Orbits ［J］． Journal of E-lectronics ＆ Information Technology，2006，28 (5):861－ 864． (in Chinese)

［<sup>14</sup>］ 余侃民，李勇军，吴继礼，等<sup>．</sup> 多层卫星网络激光星间链路空间特性仿真［J］． 电讯技术，2010，50(10):87 －92．YU Kan － min，LI Yong － jun，WU Ji － li，et al． Space Char-acteristic Simulation of Optical Inter － satellite Links inMulti － layer Satellite Networks ［J］． TelecommunicationEngineering，2010，50(10):87 － 92． (in Chinese)

［<sup>15</sup>］ 胡剑浩，李涛，吴诗其<sup>．</sup> 具有星际链路的 <sup>LEO＆MEO</sup>双层卫星网络路由策略研究［<sup>J</sup>］<sup>．</sup> 电子学报，<sup>2000</sup>，<sup>28</sup>(4):31 － 35．HU Jian － hao，LI Tao，WU Shi － qi． Routing of a LEO＆MEO Double Layer Mobile Satellite Communication Sys-tem［J］． Acta Electronica Sinica，2000，28(4):31 － 35．(in Chinese)

［<sup>16</sup>］ 吴廷勇，吴诗其<sup>．</sup> <sup>LEO/MEO</sup> 双层卫星网络层间间际链路建立策略的性能研究［<sup>J</sup>］<sup>．</sup> 电子与信息学报，

2008，30(1):67 － 71．WU Ting － yong，WU Shi － qi． Performance Analysis ofthe Inter － Layer Inter － Satellite Link EstablishmentStrategies in Two － tier LEO /MEO Satellite Networks［J］． Journal of Electronics ＆ Information Technology，2008，30(1):67 － 71． (in Chinese)

［17］ Feng S J，Ochieng Y． An Efficient Worst User Location Algorithm for the Generation of the Galileo Integrity Flag ［C］/ /Proceedings of ION GNSS 2005． Long Beach， CA:IEEE，2005:2374 － 2382．

［<sup>18</sup>］ 王振永，王平，顾学迈，等<sup>．</sup> 卫星网络中永久星间链路的设计方法研究［J］． 通信学报，2006，27(8):129 －133WANG Zhen － yong，WANG Ping，GU Xue － mai，et al．Research on design of permanent inter － satellite － linksin satellite networks［J］． Journal on Communications，2006，27(8):129 － 133． (in Chinese)

［<sup>19</sup>］ 徐勇，常青，于志坚<sup>．GNSS</sup> 星间链路测量与通信新方法研究［J］． 中国科学:技术科学，2012，42(2):230 －240XU Yong，CHANG Qing，YU Zhi － jian． On new meas-urement and communication techniques of GNSS inter －satellite links［J］． Science China: Technology Science，2012，42(2):230 － 240． (in Chinese)

［20］ Noakes M D，Cain J B，Adanls S L，et al． An adaptive link assignment algorithm for dynamically changing topologies［J］． IEEE Transactions on Communications， 1993，41(5):694 － 706．

［<sup>21</sup>］ 梁俊明<sup>．</sup> 卫星通信系统星间链路设计研究［<sup>D</sup>］<sup>．</sup> 长沙:国防科学技术大学，<sup>2006</sup>LIANG Jun － ming． Study and design of the inter satellitelinks of satellite communication system［D］． Changsha:National University of Defense Technology，2006．(in Chinese)

［22］ Abusali P A M，Tapley B D，Schutz B E． AutonomousNavigation of Global Position ystem Satellites UsingCross － Link 1V Easurements［J］． Journal of GuidanceControl and Dynamics，1998，21(2):321 － 327．

［<sup>23</sup>］ 杨力，王明洋，潘成胜<sup>．</sup>低轨层内星际链路的一种新的链路重构算法［J］． 计算机仿真，2011，28(9):79 －83YANG Li，WANG Ming － yang，PAN Cheng － sheng． No-vel Link － Reconfiguration Algorithm on Low Orbit Intra－ layer Inter － Satellite Link［J］． Computer Simulation，2011，28(9):79 － 83． (in Chinese)

［<sup>24</sup>］ 李洪鑫<sup>．</sup> 基于星间链路的多层卫星网络仿真关键技术研究［<sup>D</sup>］<sup>．</sup> 郑州:解放军信息工程大学，<sup>2011．</sup>LI Hong － xin． Research on Key Simulation Technologiesof Multilayer Satellite Networks Based on Inter － satelliteLinks ［D］． Zhengzhou:PLA Information Engineering U-niversity，2011． (in Chinese)

<sup>25</sup>］ 郑晋军，林益明，陈忠贵，等<sup>．GPS</sup> 星间链路技术及自主导航算法分析［J］． 航天器工程，2009，18(2):28 －35．

ZHENG Jin － jun，LIN Yi － ming，CHEN Zhong － gui，etal． GPS Crosslink Technology and Autonomous Naviga-tion Algorithm Analysis ［J］． Spacecraft Engineering，2009，18(2):28 － 35． (in Chinese)

［<sup>26</sup>］ 妥艳君，刘云，赫立刚<sup>．</sup> 具有星际链路的 <sup>LEO/MEO</sup> 卫星网络动态路由协议［<sup>J</sup>］<sup>．</sup> 北京交通大学学报，<sup>2010</sup>，34(2):48 － 52．TUO Yan － jun，LIU Yun，HAO Li － gang． DynamicRouting Protocol in LEO /MEO Satellite Networks withInter － Satellite Links ［J］． Journal of Beijing Jiaotong U-niversity，2010，34(2):48 － 52． (in Chinese)

［<sup>27</sup>］ 李振东，何善宝，刘崇华，等<sup>．</sup> 一种导航星座星间链路拓扑设计方法［J］． 航天器工程，2011，20(3):32 － 37．LI Zhen － dong，HE Shan － bao，LIU Chong － hua，et alAn Toplogy Design Method of Navigation Satellite Con-stellation Inter － satellite Links［J］． Spacecraft Engineer-ing，2011，20(3):32 － 37． (in Chinese)

［<sup>28</sup>］ 陈忠贵，帅平，曲广吉<sup>．</sup> 卫星导航系统技术进展(上)［J］． <sub>中国航天</sub>，2007(9):24 － 29．CHEN Zhong － gui，SHUAI Ping，QU Guang － ji． Thedevelopment of satellite navigation systemtechnology( I)［J］． Aerospace China，2007(9):24 － 29． (in Chinese)

［<sup>29</sup>］ 陈佳宝<sup>．</sup> 低轨道编队小卫星星间链路设计分析［<sup>D</sup>］<sup>．</sup>哈尔滨:哈尔滨工业大学，<sup>2009．</sup>CHENG Jia － bao． Analysis and Design of the Inter sat-ellite － links In LEO Satellites Formation Flying System［D］． Harbin: Harbin Institute of Technology，2009．(in Chinese)

［<sup>30</sup>］ 张涛<sup>．</sup> 一种用于星间链路的四臂螺旋天张的研究［<sup>D</sup>］<sup>．</sup> 西安:西安电子科技大学，<sup>2011</sup>ZHANG Tao． Study on Quadrifilar Helix Antenna for In-ter － satellite － links［D］． Xi ＇an: Xidian University，2011． (in Chinese)

［<sup>31</sup>］ 黎孝纯<sup>．</sup> 星间链路角跟踪系统校相分析［<sup>J</sup>］<sup>．</sup> 空间电<sub>子技术</sub>，2009(2):109 － 112．LI Xiao － chun． The Analysis for Phase Calibration of AngleTracking System in Inter － Satellite Links ［J］． Space Elec-tronic Technology，2009(2):109 －112． (in Chinese)

［<sup>32</sup>］ 韩松辉，归庆明，李建文，等<sup>． Walker －</sup> δ 星座星间链路的预算分析与仿真［<sup>J</sup>］<sup>．</sup> 中国空间科学技术，<sup>2012</sup>(2):10 － 16．HAN Song － hui，GUI Qing － ming，LI Jian － wen，et al．Budget Analysis and Simulation of Inter － satellite Linkin Walker － <sub>δ</sub> Constellation ［J］． Chinese Space Scienceand Technology，2012(2):10 － 16． (in Chinese)

［<sup>33</sup>］ 李迎春，朱诗兵<sup>．</sup> 星间链路自由空间传播衰减的分析［J］． <sub>科学技术与工程</sub>，2009，9(13):3840 － 3843．LI Ying － Chun，ZHU Shi － bing． Analysis of LOS ofFree Space Transmission in Inter － satellite Links Chan-nel Model［J］． Science Technology and Engineering，

2009，9(13):3840 － 3843． (in Chinese)

［<sup>34</sup>］ 刘磊，常青，李军，等<sup>．</sup> 星间异步通信链路的误码率测试技术［J］． 空间电子技术，2010(1):123 － 127LIU Lei，CHANG Qing，LI Jun，et al． Bit Error Rate TestingTechnology for the Inter － Satellite Link［J］． Space Elec-tronic Technology，2010(1):123 － 127． (in Chinese)

［<sup>35</sup>］ 王倩，王祖林，何善宝，等<sup>．</sup>动态星间链路分析及其<sup>STK/</sup>Matlab <sub>实现</sub>［J］． <sub>电讯技术</sub>，2010，50(9):19 － 23．WANG Qian，WANG Zu － lin，HE Shan － bao，et al． Dy-namic Inter － satellite Link Analysis and its STK / MatlabImplementation ［J］． Telecommunication Engineering，2010，50(9):19 － 23． (in Chinese)

［<sup>36</sup>］ 刘亚琼，杨旭海<sup>． GPS</sup> 星间链路及其数据的模拟方法研究［J］． 时间频率学报，2010，33(1):39 － 46LIU Ya － qiong，YANG Xu － hai． GPS Inter － satelliteLink and Simulation of ISL Data［J］． Journal of Timeand Frequency，2010，33(1):39 － 46． (in Chinese)

［<sup>37</sup>］ 杨磊<sup>．</sup> 基于一体化卫星网络星间链路设计及网管策略研究［<sup>D</sup>］<sup>．</sup> 武汉:华中科技大学，<sup>2009．</sup>YANG Lei． The Integrative Satellite Network － Based In-ter － satellite Link Design and Satellite Network Manage-ment Strategies Research［D］． Wuhan: Huazhong Uni-versity of Science ＆ Technology，2009． (in Chinese)

［<sup>38</sup>］ 菀喆，张军，柳重堪<sup>．</sup> 一种基于链路稳定性模型的<sup>LEO/MEO</sup> 双层卫星网星间链路的设计方法［<sup>J</sup>］<sup>．</sup> 电<sub>子与信息学报</sub>，2006，28(6):1086 － 1090．

YUAN Zhe，ZHANG Jun，LIU Chong － kan． A Link sta-bility － Based Inter satellite Link Design Strategy forLEO /MEO Two － Layered Satellite Networks［J］． Jour-nal of Electronics ＆ Information Technology，2006，28(6):1086 － 1090． (in Chinese)

## 作者简介:

![](../../images/images_Luo_2014_ISL_Technology_Review/b8aad5df9e95e38a0989791aab49f048b2104496df12f276791660761f31af1d.jpg)

罗大成(1981—)，男，湖南新邵人，2010年于第二炮兵工程学院获博士学位，现为讲师，主要研究方向为惯导<sup>/</sup>卫星组合导航技术和星间链路技术;

LUO da － cheng was born in Xinshao，Hunan Province，in 1981． He received the Ph． D． degree from the Second Artillery Engineering

College in 2010． He is now a lecturer． His research concerns GPS and INS integrated system and inter － satellite links

Email:luodcheng@ 163． com

刘 岩(<sup>1973</sup>—)，男，江苏镇江人，<sup>2006</sup> 年获博士学位，现为副教授 硕士研究生导师，主要研究方向为导航 制导与控制 复杂系统建模与仿真

LIU Yan was born in Zhenjiang，Jiangsu Province，in 1973． He received the Ph． D． degree in 2006． He is now an associate professor and also the instructor of graduate students． His research interests include navigation，guidance and control，complex system modeling and simulation

Email:68169371@ qq． com