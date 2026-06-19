# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Complete reference list for 29 included RCTs
# Background refs [1]-[19] remain unchanged
# Included studies start from [20]

included_refs = [
    # R01
    '[20] Ramirez-Campillo R, Meylan CMP, Alvarez-Lepin C, et al. Effects of in-season low-volume plyometric training on explosive actions and endurance of young soccer players. J Strength Cond Res. 2015;29(10):2905-2912. doi:10.1519/JSC.0000000000000665. PMID:25632706.',

    # R02
    '[21] Ramirez-Campillo R, Burgos CH, Henriquez-Olguin C, et al. Effect of unilateral, bilateral, and combined plyometric training on explosive and endurance performance of young soccer players. J Strength Cond Res. 2015;29(5):1317-1328. doi:10.1519/JSC.0000000000000811. PMID:25789497.',

    # R03
    '[22] Ramirez-Campillo R, Henriquez-Olguin C, Burgos C, et al. Effect of progressive volume-based overload during plyometric training on explosive and endurance performance in young soccer players. J Strength Cond Res. 2015;29(7):1884-1893. doi:10.1519/JSC.0000000000000864. PMID:26010692.',

    # R04: Palma-Munoz (published 2021, listed as 2018 in screening)
    '[23] Palma-Munoz I, Ramirez-Campillo R, Azocar-Gallardo J, et al. Effects of progressed and non-progressed volume-based overload plyometric training on components of physical fitness and body composition variables in youth male basketball players. J Strength Cond Res. 2021;35(6):1642-1649. doi:10.1519/JSC.0000000000002950. PMID:34027922.',

    # R05
    '[24] Ramirez-Campillo R, Alvarez C, Henriquez-Olguin C, et al. Effects of plyometric training on endurance and explosive strength performance in competitive middle- and long-distance runners. J Strength Cond Res. 2014;28(1):97-104. doi:10.1519/JSC.0b013e318295ef62. PMID:24149707.',

    # R06
    '[25] Van Roie E, Walker S, Van Driessche S, Delabastita T, Vanwanseele B, Delecluse C. An age-adapted plyometric exercise program improves dynamic strength, jump performance and functional capacity in older men either similarly or more than traditional resistance training. PLoS One. 2020;15(8):e0237921. doi:10.1371/journal.pone.0237921. PMID:32810152.',

    # R07
    '[26] Chang CH, Chen CY, Lau HT. The effects of four-week plyometric training on delaying muscle fatigue in youth rowers. Sci Rep. 2025;15(1):22141. doi:10.1038/s41598-025-09673-w. PMID:40595375.',

    # R08
    '[27] Asadi A, Ramirez-Campillo R, Meylan C, Nakamura FY, Canas-Jamett R, Izquierdo M. Effects of volume-based overload plyometric training on maximal-intensity exercise adaptations in young basketball players. J Sports Med Phys Fitness. 2017;57(12):1557-1563. doi:10.23736/S0022-4707.16.06640-8. PMID:27792040.',

    # R09
    '[28] Blazevich AJ, Gill ND, Bronks R, Newton RU. Training-specific muscle architecture adaptation after 5-wk training in athletes. Med Sci Sports Exerc. 2003;35(12):2013-2022. doi:10.1249/01.MSS.0000099092.83611.20. PMID:14669938.',

    # R10
    '[29] Byrne PJ, Moran K, Rankin P, Kinsella S. Effect of a six-week plyometric training program on the acceleration, agility, leg power and strength of collegiate Gaelic footballers. J Strength Cond Res. 2010;24(10):2633-2641. doi:10.1519/JSC.0b013e3181e38125. PMID:20613646.',

    # R11
    '[30] Sedano Campo S, Vaeyens R, Philippaerts RM, Redondo JC, de Benito AM, Cuadrado G. Effects of lower-limb plyometric training on body composition, explosive strength, and kicking speed in female soccer players. J Strength Cond Res. 2009;23(6):1714-1722. doi:10.1519/JSC.0b013e3181a38984. PMID:19528837.',

    # R12
    '[31] Chelly MS, Ghenem MA, Abid K, Hermassi S, Tabka Z, Shephard RJ. Effects of in-season short-term plyometric training program on leg power, jump- and sprint performance of soccer players. J Strength Cond Res. 2010;24(10):2670-2676. doi:10.1519/JSC.0b013e3181e2728f. PMID:20844458.',

    # R13
    '[32] Idrizovic K, Gjinovci B, Sekulic D, Uljevic O, Joao PV, Spasic M, Sattler T. The effects of 3-month skill-based and plyometric conditioning on fitness parameters in junior female volleyball players. Pediatr Exerc Sci. 2018;30(3):353-363. doi:10.1123/pes.2017-0178. PMID:29478378.',

    # R14
    '[33] Jlid MC, Coquart J, Maffulli N, Paillard T, Bisciotti GN, Chamari K. Multidirectional plyometric training: very efficient way to improve vertical jump performance, change of direction performance and dynamic postural control in young soccer players. Front Physiol. 2019;10:1462. doi:10.3389/fphys.2019.01462. PMID:31736978.',

    # R15
    '[34] Jlid MC, Coquart J, Maffulli N, Paillard T, Bisciotti GN, Chamari K. Effects of in season multi-directional plyometric training on vertical jump performance, change of direction speed and dynamic postural control in U-21 soccer players. Front Physiol. 2020;11:374. doi:10.3389/fphys.2020.00374. PMID:32431621.',

    # R16
    '[35] Khlifa R, Aouadi R, Hermassi S, Chelly MS, Jlid MC, Hbacha H, Castagna C. Effects of a plyometric training program with and without added load on jumping ability in basketball players. J Strength Cond Res. 2010;24(11):2955-2961. doi:10.1519/JSC.0b013e3181e37fbe. PMID:20938357.',

    # R17
    '[36] Kijowksi KN, Capps CR, Goodman CL, Erickson TM, Knorr DP, Triplett NT, Awelewa OO, McBride JM. Short-term resistance and plyometric training improves eccentric phase kinetics in jumping. J Strength Cond Res. 2015;29(8):2186-2196. doi:10.1519/JSC.0000000000000904. PMID:26203736.',

    # R18
    '[37] Laurent C, Baudry S, Duchateau J. Comparison of plyometric training with two different jumping techniques on Achilles tendon properties and jump performances. J Strength Cond Res. 2020;34(6):1503-1510. doi:10.1519/JSC.0000000000003604. PMID:32271290.',

    # R19
    '[38] Michailidis Y, Tabouris A, Metaxas T. Effects of plyometric and directional training on physical fitness parameters in youth soccer players. Int J Sports Physiol Perform. 2019;14(3):392-398. doi:10.1123/ijspp.2018-0545. PMID:30204520.',

    # R20
    '[39] Negra Y, Chaabene H, Sammoud S, Bouguezzi R, Abbes M, Hachana Y, Granacher U. Effects of plyometric training on physical fitness in prepuberal soccer athletes. Int J Sports Med. 2017;38(5):370-377. doi:10.1055/s-0042-122337. PMID:28315285.',

    # R21
    '[40] Potdevin FJ, Alberty ME, Chevutschi A, Pelayo P, Sidney MC. Effects of a 6-week plyometric training program on performances in pubescent swimmers. J Strength Cond Res. 2011;25(1):80-86. doi:10.1519/JSC.0b013e3181fef720. PMID:21157388.',

    # R22
    '[41] Ramirez-Campillo R, Alvarez C, Gentil P, Loturco I, Sanchez-Sanchez J, Izquierdo M, Moran J, Nakamura FY, Chaabene H, Granacher U. Sequencing effects of plyometric training applied before or after regular soccer training on measures of physical fitness in young players. J Strength Cond Res. 2020;34(7):1959-1966. doi:10.1519/JSC.0000000000002525. PMID:29570574.',

    # R23: Rensing – German article, exact PMID/DOI to be verified
    '[42] Rensing N, Bartsch J, Rembitzki I, et al. Trainingseffekte eines reaktiven Sprungkrafttrainings bei Basketballspielern [Training effects of reactive jump training in basketball players]. Dtsch Z Sportmed. 2015;66(10):272-278. doi:10.5960/dzsm.2015.198. [PMID:待PubMed验证]',

    # R24
    '[43] Rubley MD, Haase AC, Holcomb WR, Girouard TJ, Tandy RD. The effect of plyometric training on power and kicking distance in female adolescent soccer players. J Strength Cond Res. 2011;25(1):129-134. doi:10.1519/JSC.0b013e3181b94a3d. PMID:19966586.',

    # R26
    '[44] Santos EJAM, Janeira MAAS. The effects of plyometric training followed by detraining and reduced training periods on explosive strength in adolescent male basketball players. J Strength Cond Res. 2011;25(2):441-452. doi:10.1519/JSC.0b013e3181b62be3. PMID:20453686.',

    # R27
    '[45] Toumi H, Best TM, Martin A, FGuyer S, Poumarat G. Effects of eccentric phase velocity of plyometric training on the vertical jump. Int J Sports Med. 2004;25(5):391-398. doi:10.1055/s-2004-815843. PMID:15241721.',

    # R29
    '[46] Vescovi JD, Canavan PK, Hasson S. Effects of a plyometric program on vertical landing force and jumping performance in college women. Phys Ther Sport. 2008;9(4):185-192. doi:10.1016/j.ptsp.2008.08.001. PMID:19083719.',

    # R30
    '[47] Yanci J, Castillo D, Iturricastillo A, Ayarra R, Nakamura FY. Effects of two different volume-equated weekly distributed short-term plyometric training programs on futsal players physical performance. J Strength Cond Res. 2017;31(7):1787-1794. doi:10.1519/JSC.0000000000001644. PMID:27662489.',

    # R31
    '[48] Zubac D, Simunic B. Skeletal muscle contraction time and tone decrease after 8 weeks of plyometric training. J Strength Cond Res. 2017;31(6):1610-1619. doi:10.1519/JSC.0000000000001626. PMID:28538312.',
]

print(f"生成了 {len(included_refs)} 条纳入研究的参考文献")
print()
print("=== 纳入研究的完整参考文献 [20]-[48] ===")
print()
for ref in included_refs:
    print(ref)
    print()

# Mapping
print("=== 引用编号映射 ===")
print("R01->[20] R02->[21] R03->[22] R04->[23] R05->[24]")
print("R06->[25] R07->[26] R08->[27] R09->[28] R10->[29]")
print("R11->[30] R12->[31] R13->[32] R14->[33] R15->[34]")
print("R16->[35] R17->[36] R18->[37] R19->[38] R20->[39]")
print("R21->[40] R22->[41] R23->[42] R24->[43] R26->[44]")
print("R27->[45] R29->[46] R30->[47] R31->[48]")
print()
print("总计: 19条背景引用 [1]-[19] + 29条纳入研究引用 [20]-[48] = 48条")
print()
print("注意: R04的PubMed年份是2021，筛选文件中列为2018。R23(Rensing)的PMID需要从PubMed直接验证。")
