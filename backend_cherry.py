import os.path
import time

import cherrypy
from scipy.special import softmax
from demo import compute_single_label, load_model_to_mem,load_demo_input, comput_bart_single_label, loading_bart_model, loading_bart_fever_rte_model, compute_bart_fever_rte_single_label
from ESA import load_ESA_sparse_matrix, load_ESA_word2id, ESA_cosine
import argparse

print("")
print("Loading classifer...")

parser = argparse.ArgumentParser()
parser.add_argument("--ZEROSHOT_MODELS",
                            default=None,
                            type=str,
                            help="dir to save pretrained models")
parser.add_argument("--ZEROSHOT_RESOURCES",
                            default=None,
                            type=str,
                            help="dir to save ESA files")
args = parser.parse_args()
global cache
cache = load_model_to_mem(args.ZEROSHOT_MODELS)
bart_cache = loading_bart_fever_rte_model(args.ZEROSHOT_MODELS)
bart_model, bart_tokenizer = loading_bart_model()
print("Load models succeed")
ESA_sparse_matrix = load_ESA_sparse_matrix(args.ZEROSHOT_RESOURCES).tocsr()
ESA_word2id = load_ESA_word2id(args.ZEROSHOT_RESOURCES)


class StringPredicter(object):
    @cherrypy.expose
    def index(self):

        return open('public/0shot.html')

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def predict(self):

        start_time = time.time()
        cherrypy.response.headers['Content-Type'] = 'application/json'
        data = cherrypy.request.json
        # model_list = ["MNLI", "FEVER", "RTE"]  # FIXED !
        ESA_cosin_simlarity_list = ESA_cosine(data["text"], data["labels"], ESA_sparse_matrix, ESA_word2id)
        result = {
            "text": data["text"],
            "models": data["models"],
            "labels": data["labels"],
            "sorted_output": [],
        }
        for idx,label in enumerate(data["labels"]):
            if label != None:
                each_label_result = {"label": label, 'Sum': 0.}
                if idx < len(data["descriptions"]) and data["descriptions"][idx] != None: #means user added descriptions
                    each_label_result['label'] = label + ' + ' + '{}...'.format(data["descriptions"][idx][:15])
                    label = label + ' | ' + data["descriptions"][idx]
                    result["labels"][idx] = label
                if label not in result["labels"][:idx]:
                    test_examples = load_demo_input(data["text"], label.split(' | '))
                    for model_name in data["models"]:
                        if model_name in ["Bert-MNLI", "Bert-FEVER", "Bert-RTE"]:
                            model = cache[model_name][0]
                            tokenizer = cache[model_name][1]
                            each_label_result[model_name] = round((100. * compute_single_label(test_examples, model, tokenizer)), 4)
                            each_label_result['Sum'] += each_label_result[model_name]
                        if model_name == "ESA":
                            each_label_result[model_name] = ESA_cosin_simlarity_list[idx]
                            each_label_result['Sum'] += each_label_result[model_name]
                        if model_name == "Bart-MNLI":
                            each_label_result[model_name] = round((100. * comput_bart_single_label(data['text'], label,bart_model, bart_tokenizer)), 4)
                            each_label_result['Sum'] += each_label_result[model_name]
                        if model_name in ["Bart-FEVER", "Bart-RTE"]:
                            model = bart_cache[model_name][0]
                            tokenizer = bart_cache[model_name][1]
                            each_label_result[model_name] = round(
                                (100. * compute_bart_fever_rte_single_label(test_examples, model, tokenizer)), 4)
                            each_label_result['Sum'] += each_label_result[model_name]
                    # each_label_result_with_ave['Average'] = round((each_label_result_with_ave['Average'] / len(data["models"])),3 )
                    result["sorted_output"].append(each_label_result)
        result["sorted_output"] = sorted(result["sorted_output"], key= lambda i: i['Sum'])
        # print("{}Labels, {}Models, Response time:{:0.4f}s".format(len(data["labels"]), len(data["models"]), (time.time() - start_time)))
        # print(result)
        return result


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())

        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        },
        '/css':
            {'tools.staticdir.on': True,
             'tools.staticdir.dir': "./public/css"
             },
        '/js':
            {'tools.staticdir.on': True,
             'tools.staticdir.dir': "./public/js"
             },

    }
    print("Starting rest service...")
    config = {'server.socket_host': '0.0.0.0'}
    cherrypy.config.update(config)
    # cherrypy.config.update({'server.socket_port': 8081})  #match the port on dickens server
    cherrypy.config.update(
        {'server.socket_host': 'dickens.seas.upenn.edu', 'server.socket_port': 4007, 'cors.expose.on': True})
    cherrypy.quickstart(StringPredicter(), '/', conf)