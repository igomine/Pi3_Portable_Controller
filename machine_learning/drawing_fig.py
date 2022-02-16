import argparse
import numpy as np
import datetime
# 引用 paddle inference 预测库
import paddle.inference as paddle_infer

normal_data_path = "D:\\zhouruidong\\coupleingData10.25-11.5\\"
model_file_path = "D:\\zhouruidong\\coupleingData10.25-11.5\\finalmodel\\export_model.pdmodel"
params_file_path = "D:\\zhouruidong\\coupleingData10.25-11.5\\finalmodel\\export_model.pdiparams"

traindata_mean =[
    [ 9.36589088,  8.66036243,  8.37729343,  8.35937399,  9.65899767,  8.51965566,
   8.73869436,  9.3772369 ,  9.33404936, 10.17073939 , 9.00457071, 8.62470121,
   9.44834938,  9.90131791,  8.96865915,  7.87917501],
 [ 9.52820757,  8.74851412,  8.25296369,  8.30060889 , 9.8648653,   8.47470767,
   8.87088152,  9.36820047,  9.40086569, 10.2257817  , 9.23120841,  8.81692939,
   9.60056367, 10.07613541,  8.87479811,  7.78917404],
 [ 9.67196686,  8.84646133,  8.14027069,  8.24099587 ,10.06688901 , 8.47105756,
   9.00142936,  9.38861522,  9.50062989, 10.32605465 , 9.45496318  ,9.01132987,
   9.73863783, 10.24899057,  8.80378254,  7.71614768],
 [ 9.78568544,  8.91179986,  8.05949189,  8.20451095 ,10.23208864 , 8.5097713,
   9.12395019,  9.44262388,  9.63901092, 10.47711415 , 9.64573777 , 9.18152012,
   9.84467666, 10.37391789,  8.75630693,  7.6696815 ],
 [ 9.82591737,  8.93193197,  8.02873248,  8.18087409 ,10.33161864 , 8.59912624,
   9.19633859,  9.52308773,  9.81688094, 10.68191582 , 9.77075392 , 9.29551328,
   9.89132857, 10.43084179,  8.74797306,  7.65971639],
 [ 9.78782544,  8.90227889,  8.03785774,  8.17358195 ,10.36110214 , 8.7301909,
   9.21241682,  9.62706732, 10.01983332, 10.9292913  , 9.82052297 , 9.35052329,
   9.87773758, 10.41494121,  8.77769074,  7.6837328 ],
 [ 9.67989696,  8.83383132,  8.09699431,  8.18084986 ,10.32569933 , 8.8934928,
   9.18589702,  9.74416144, 10.22241424, 11.20042477 , 9.80409749 , 9.3542057,
   9.82257413, 10.33946799,  8.84916661 , 7.74941049],
 [ 9.53366658,  8.74787615,  8.1903789  , 8.21707636 ,10.24039828 , 9.06737354,
   9.1214468 ,  9.85867143, 10.41328574 ,11.45870211 , 9.72999709 , 9.31546773,
   9.73304154, 10.22646812,  8.9487693  , 7.83826475],
 [ 9.35893792,  8.63230829,  8.29911493 , 8.26128949 ,10.10012759 , 9.21143162,
   9.0158602 ,  9.94612863, 10.55795756 ,11.655073   , 9.60670909 , 9.22843853,
   9.60916403, 10.07618386,  9.05362911 , 7.93215001],
 [ 9.18736675,  8.51658699,  8.40103527 , 8.30446088 , 9.94422282 , 9.31845565,
   8.88812262, 10.00489373, 10.64264487, 11.78681601 , 9.46890141 , 9.11701337,
   9.49333775,  9.93369242,  9.13760579 , 8.02374184],
 [ 9.02813489,  8.41592642,  8.48510886  ,8.33658505 , 9.77907972 , 9.35620841,
   8.76069191, 10.00826927, 10.65190742, 11.81860101 , 9.3352849  , 9.00201886,
   9.38537696,  9.80541379,  9.20086084,  8.08723109],
 [ 8.89284676,  8.32524711,  8.54579592,  8.35385038 , 9.60976161 , 9.33540603,
   8.63404451,  9.95582725, 10.59045319, 11.75719523 , 9.20730506 , 8.89892758,
   9.29580399,  9.69394825,  9.23400252,  8.12739841],
 [ 8.78499096,  8.25326248,  8.58223238,  8.35897829 , 9.44760643 , 9.25887493,
   8.51607824,  9.86467957, 10.46613153, 11.61693262 , 9.09472511 , 8.79399509,
   9.21808579,  9.61444538,  9.23490697,  8.13419795],
 [ 8.71244912,  8.21350701,  8.60143582,  8.36781284 , 9.30929001 , 9.17023871,
   8.41096001,  9.76796789, 10.30797371, 11.43080141 , 8.98434976 , 8.69037082,
   9.15651851,  9.5552442 ,  9.22415854,  8.13799341],
 [ 8.65319142,  8.1780073 ,  8.61669035,  8.37515343 , 9.18360359 , 9.06863331,
   8.32782318,  9.66946347, 10.13155727, 11.2222285  , 8.8666419  , 8.58521222,
   9.10615996,  9.49800536,  9.21535629,  8.14368661],
 [ 8.62685736,  8.16485238,  8.64234608,  8.39124782  ,9.08238581 , 8.98600523,
   8.26011855,  9.58688384,  9.96711674, 11.01909846  ,8.74724627 , 8.47585438,
   9.06747044,  9.44445701,  9.21386233,  8.15429776],
 [ 8.59995801,  8.15577557,  8.67692519,  8.41591027 , 8.98264584 , 8.92073131,
   8.21177079,  9.51805672,  9.80069772, 10.8285419  , 8.62494347 , 8.35967278,
   9.01290458,  9.38748466,  9.21585697,  8.16362491],
 [ 8.58830512,  8.15580787,  8.70735351,  8.45019058 , 8.9126074  , 8.87210091,
   8.1771836 ,  9.47303605,  9.66330189, 10.66656438,  8.50669455 , 8.25105788,
   8.97888268,  9.33737645,  9.22411816,  8.18518638],
 [ 8.57533594,  8.16714581,  8.75155049,  8.49624491 , 8.86181278 , 8.84563764,
   8.16722657,  9.46004264,  9.54843659, 10.5397797 ,  8.4139237  , 8.1629385,
   8.94689579,  9.29857387,  9.25318981,  8.21043026]]
traindata_std = [
    [11.32331002, 10.19142225, 10.65793391, 10.60507399, 11.75085356, 10.47783453,
  10.30083095, 11.9875384 , 11.37513909, 12.59183497, 10.91365286, 10.44848927,
  11.38139672, 12.06081161, 11.13321342,  9.63205697],
 [10.73129147,  9.63106595, 10.13478234, 10.14953957, 11.29848578,  9.74656931,
   9.84462705, 11.41008426, 10.66992812, 11.81775425, 10.46908211, 10.03421604,
  10.92111863, 11.57815142, 10.52552083,  9.01034901],
 [10.11433681,  9.05176634,  9.59651951,  9.70147182, 10.82088495,  8.9967909,
   9.36432263, 10.82066954,  9.90238631, 10.99018439,  9.96779686,  9.57594706,
  10.39299952, 11.0465731 ,  9.88595342,  8.33554934],
 [ 9.52733363,  8.47493515,  9.07651573,  9.26514862 ,10.35628304,  8.27478461,
   8.89428445, 10.26478233,  9.15045029, 10.18535306 , 9.44267485,  9.10372897,
   9.84943031, 10.48577197,  9.26110934,  7.66588552],
 [ 9.04710126,  8.00544467,  8.66335012,  8.92139605 , 9.97192465,  7.70783966,
   8.50583675,  9.81357414,  8.51054551,  9.49905214 , 8.95254561,  8.66393093,
   9.33942579,  9.95692226,  8.71242613,  7.09738012],
 [ 8.68589422,  7.65390597,  8.38222895,  8.68902056 , 9.68086647,  7.36680092,
   8.19787199,  9.51868888,  8.05766157,  9.03938168 , 8.53022454,  8.29098401,
   8.89345567,  9.50204248,  8.33015743,  6.69401741],
 [ 8.43600499,  7.44189529,  8.28536835,  8.56668909 , 9.49026021,  7.28697528,
   8.02335075,  9.39400604,  7.8325205 ,  8.84718584 , 8.20865238,  8.00959084,
   8.55403394,  9.16402473,  8.15095102,  6.51858237],
 [ 8.3250143 ,  7.37937399,  8.34802887,  8.59085252 , 9.40473028,  7.45031072,
   7.97183499,  9.44919089,  7.86752498,  8.93103553 , 8.01878944,  7.85889125,
   8.34676642,  8.95728577,  8.17449473,  6.56766352],
 [ 8.32617548,  7.42407478,  8.53221455,  8.71845542 , 9.42019444,  7.76732609,
   8.00883918,  9.61982098,  8.10449335,  9.21189293 , 7.9457915 ,  7.81452801,
   8.27204484,  8.88405918,  8.3539953 ,  6.78953913],
 [ 8.40695297,  7.55657641,  8.78660984,  8.90072517 , 9.48636043,  8.1812361,
   8.10980452,  9.87095456,  8.47026371,  9.63321093 , 7.99278852,  7.86981544,
   8.33155883,  8.93331281,  8.62830694,  7.12871506],
 [ 8.53091079,  7.7310277 ,  9.09188926,  9.11579255 , 9.59323786,  8.59571374,
   8.26752561, 10.14732851,  8.89155022, 10.09762262 , 8.14687786,  8.009877,
   8.49324768,  9.09039549,  8.96649222,  7.50995513],
 [ 8.67376678,  7.91334759,  9.398996  ,  9.35344459 , 9.71332752,  8.98170002,
   8.44136613, 10.42520652,  9.31402299, 10.56397598 , 8.36568871,  8.21552824,
   8.71316168,  9.32167872,  9.30188349,  7.88347354],
 [ 8.81908341,  8.11210497,  9.69411551,  9.57258768 , 9.83647718,  9.33331133,
   8.61897951, 10.68372416,  9.71599747, 10.98423158 , 8.63565069,  8.45668347,
   8.98651392,  9.59801666,  9.63635009,  8.20948329],
 [ 8.96007562,  8.30039676,  9.96226725,  9.79166924 , 9.95917688,  9.64390708,
   8.78928899, 10.92265224, 10.07483859, 11.36493127 , 8.92431698,  8.70889244,
   9.27555772,  9.90036696,  9.93449531,  8.50358568],
 [ 9.07024166,  8.43579954, 10.16611251,  9.97735333 ,10.05401523,  9.87192014,
   8.92071905, 11.12402906, 10.3942115 , 11.68924608 , 9.21738322,  8.96732969,
   9.55058532, 10.17577186, 10.18715811,  8.7670005 ],
 [ 9.23784552,  8.60793376, 10.38374932, 10.17981678 ,10.18600966, 10.12601043,
   9.08231016, 11.34501966, 10.70252137, 11.9936045  , 9.51703926,  9.22741191,
   9.8523154 , 10.45679045, 10.44387063,  8.99911562],
 [ 9.38474356,  8.78767676, 10.58224435, 10.32477499 ,10.28824029, 10.37293794,
   9.25686422, 11.52263942, 10.95854295, 12.25716038 , 9.79527455,  9.45917864,
  10.12495873, 10.71678403, 10.6939985 ,  9.1872188 ],
 [ 9.46966366,  8.89319547, 10.6452935 , 10.38045053 ,10.31864345, 10.52698209,
   9.33473589, 11.59487724, 11.14284418, 12.44124068 ,10.01449723,  9.62753179,
  10.32691135 ,10.90228058, 10.83387373 , 9.33700645],
 [ 9.4928957  , 8.97716883, 10.65100509 ,10.38775114 ,10.33169424, 10.64134754,
   9.3519457  ,11.66066224, 11.28610288 ,12.5693798  ,10.18163763,  9.7408501,
  10.50078552, 11.06645986, 10.92687179 , 9.45198295]]

positive_data_path = normal_data_path + "2021_10_25_17_24_3000_spped_p.npz"

negative_data_path_1 = normal_data_path + "2021_10_28_14_36_3000_spped_n.npz"
negative_data_path_2 = normal_data_path + "2021_10_28_16_50_3000_spped_n.npz"
negative_data_path_3 = normal_data_path + "2021_10_29_12_35_3000_spped_n.npz"
negative_data_path_4 = normal_data_path + "2021_10_29_13_06_3000_spped_n.npz"
negative_data_path_5 = normal_data_path + "2021_10_29_16_28_3000_spped_n.npz"
negative_data_path_6 = normal_data_path + "2021_11_01_17_52_3000_spped_n.npz"
negative_data_path_7 = normal_data_path + "2021_11_05_14_40_3000_spped_n.npz"
negative_data_path_8 = normal_data_path + "2021_11_05_16_42_3000_spped_n.npz"
negative_data_path_9 = normal_data_path + "2021_11_05_17_41_3000_spped_n.npz"

positive_data = np.load(positive_data_path)
posdata = positive_data['arr_0']
fake_pos = posdata[27355]
negative_data_1 = np.load(negative_data_path_1)
negative_data_1 = negative_data_1['arr_0']
# print("negative_data_1.shape", negative_data_1.shape)
fake_neg = negative_data_1[573]

def main():
    print("begin", datetime.datetime.now())
    args = parse_args()
    # 创建 config
    config = paddle_infer.Config(args.model_file, args.params_file)
    # config = paddle_infer.Config(model_file_path, params_file_path)
    # 根据 config 创建 predictor
    predictor = paddle_infer.create_predictor(config)

    # 获取输入的名称
    input_names = predictor.get_input_names()
    input_handle = predictor.get_input_handle(input_names[0])

    fake_input = np.array(fake_pos)
    # print("fake_input.shape", fake_input.shape)
    # print("fake_input", fake_input)

    fake_input = (fake_input - traindata_mean)/traindata_std
    # print("fake_input,std", fake_input)
    # fake_input = np.reshape(fake_input, (1, 19, 16))
    fake_input = np.expand_dims(fake_input, axis=0)
    # print("fake_input.shape", fake_input.shape)
    # copy_input = fake_input
    # for i in range(31):
    #     fake_input = np.append(fake_input, copy_input, axis=0)
    fake_input = np.float32(fake_input)

    # print("fake_input.dtype", fake_input.dtype)

    input_handle.reshape([args.batch_size, 19, 16])
    input_handle.copy_from_cpu(fake_input)
    print("predictor.run() begin", datetime.datetime.now())
    # 运行predictor
    predictor.run()
    print("predictor.run() end", datetime.datetime.now())

    # 获取输出
    output_names = predictor.get_output_names()
    output_handle = predictor.get_output_handle(output_names[0])
    output_data = output_handle.copy_to_cpu()  # numpy.ndarray类型

    print("end", datetime.datetime.now())

    print("Output data size is {}".format(output_data.size))
    print("Output data shape is {}".format(output_data.shape))
    print("output_data", output_data)
    print("=====================")
    if output_data[0][0] > output_data[0][1]:
        print("Coupling is Not Dectected")
    else:
        print("Coupling is  Dectected")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_file", type=str, help="model filename")
    parser.add_argument("--params_file", type=str, help="parameter filename")
    parser.add_argument("--batch_size", type=int, default=1, help="batch size")
    return parser.parse_args()


if __name__ == "__main__":
    main()