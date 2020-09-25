#conding=utf8
import os
import json
import codecs
import argparse
import nltk
from collections import defaultdict, Counter
import numpy as np
from scipy.sparse import coo_matrix, csr_matrix, lil_matrix
import time
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity
'''seven global variables'''
title2id={} #5903490+1
title_size = 0
word2id={} #6161731+1
word_size = 0
# WordTitle2Count= lil_matrix((298099,40000))#(6113524, 5828563))
WordTitle2Count= lil_matrix((6161731, 5903486))#(6113524, 5828563))
Word2TileCount=defaultdict(int)
fileset=set()

def scan_all_json_files(rootDir):
    global fileset
    for lists in os.listdir(rootDir):
        path = os.path.join(rootDir, lists)
        if os.path.isdir(path):
            scan_all_json_files(path)
        else: # is a file
            fileset.add(path)

def load_json():
    global title2id
    global word2id
    global title_size
    global word_size
    global WordTitle2Count
    global Word2TileCount
    global fileset

    json_file_size = 0
    wiki_file_size = 0
    for json_input in fileset:
        json_file_size+=1
        print('\t\t\t', json_input)
        with codecs.open(json_input, 'r', 'utf-8') as f:
            for line in f:
                try:
                    line_dic = json.loads(line)
                except ValueError:
                    continue
                title = line_dic.get('title')
                title_id = title2id.get(title)
                if title_id is None: # if word was not in the vocabulary
                    title_id=title_size  # id of true words starts from 1, leaving 0 to "pad id"
                    title2id[title]=title_id
                    title_size+=1

                content = line_dic.get('text')
                '''this tokenizer step should be time-consuming'''
                tokenized_text = nltk.word_tokenize(content)
                word_id_set = set()
                for word in tokenized_text:
                    if word.isalpha():
                        word_id = word2id.get(word)
                        if word_id is None:
                            word_id = word_size
                            word2id[word]=word_id
                            word_size+=1
                        WordTitle2Count[str(word_id)+':'+str(title_id)]+=1
                        word_id_set.add(word_id)
                for each_word_id in word_id_set:
                    Word2TileCount[str(each_word_id)]+=1 #this word meets a new title
                wiki_file_size+=1
                print(json_file_size, '&',wiki_file_size, '...over')
                # if wiki_file_size ==4:
                #     return

def load_tokenized_json(data_dir):
    '''
    we first tokenzie tool output json files into a single json file "tokenized_wiki.txt"
    now we do statistics on it
    '''
    start_time = time.time()
    global title2id
    global word2id
    global title_size
    global word_size
    global WordTitle2Count
    global Word2TileCount
    # global fileset

    route = '{}/0shot/BenchmarkingZeroShot/dataset/wikipedia/parsed_output/tokenized_wiki/'.format(data_dir)
    wiki_file_size = 0
    with codecs.open(route+'tokenized_wiki.txt', 'r', 'utf-8') as f:
        for line in f:
            try:
                line_dic = json.loads(line)
            except ValueError:
                continue
            title = line_dic.get('title')
            title_id = title2id.get(title)
            if title_id is None: # if word was not in the vocabulary
                title_id=title_size  # id of true words starts from 1, leaving 0 to "pad id"
                title2id[title]=title_id
                title_size+=1

            # content = line_dic.get('text')
            tokenized_text = line_dic.get('text').split()
            word2tf=Counter(tokenized_text)
            for word, tf in word2tf.items():
                word_id = word2id.get(word)
                if word_id is None:
                    word_id = word_size
                    word2id[word]=word_id
                    word_size+=1
                WordTitle2Count[word_id, title_id]=tf
                Word2TileCount[word_id]+=1 #this word meets a new title
            wiki_file_size+=1
            if wiki_file_size%10000==0:
                print(wiki_file_size, '...over')
            # if wiki_file_size ==4000:
            #     break
    f.close()
    print('load_tokenized_json over.....words:', word_size, ' title size:', title_size)
    WordTitle2Count = divide_sparseMatrix_by_list_row_wise(WordTitle2Count, Word2TileCount.values())
    print('divide_sparseMatrix_by_list_row_wise....over')
    spend_time = (time.time()-start_time)/60.0
    print(spend_time, 'mins')

def store_ESA(data_dir):
    start_time = time.time()
    global title2id
    global word2id
    global WordTitle2Count
    global Word2TileCount
    route = '{}/0shot/BenchmarkingZeroShot/dataset/wikipedia/parsed_output/statistics_from_json/'.format(data_dir)
    with open(route+'title2id.json', 'w') as fp1:
        json.dump(title2id, fp1)
    with open(route+'word2id.json', 'w') as fp2:
        json.dump(word2id, fp2)
    # with open(route+'WordTitle2Count.json', 'w') as f3:
    #     json.dump(WordTitle2Count, f3)
    '''note that WordTitle2Count is always a sparse matrix, not a dictionary'''
    sparse.save_npz(route+"ESA_Sparse_v1.npz", WordTitle2Count)
    print('ESA sparse matrix stored over, congrats!!!')
    with open(route+'Word2TileCount.json', 'w') as f4:
        json.dump(Word2TileCount, f4)
    print('store ESA over')
    spend_time = (time.time()-start_time)/60.0
    print(spend_time, 'mins')


def tokenize_filter_tokens(data_dir):
    global fileset
    route = '/Users/yangjinrui/Documents/upenn/0shot/BenchmarkingZeroShot/dataset/wikipedia/parsed_output/tokenized_wiki/'.format(data_dir)
    writefile = codecs.open(route+'tokenized_wiki.txt' ,'a+', 'utf-8')
    json_file_size = 0
    wiki_file_size = 0
    for json_input in fileset:
        json_file_size+=1
        print('\t\t\t', json_input)
        with codecs.open(json_input, 'r', 'utf-8') as f:
            for line in f:
                try:
                    line_dic = json.loads(line)
                except ValueError:
                    continue
                # title = line_dic.get('title')
                content = line_dic.get('text')
                tokenized_text = nltk.word_tokenize(content)
                new_text = []
                for word in tokenized_text:
                    if word.isalpha():
                        new_text.append(word)
                line_dic['text']=' '.join(new_text)
                json.dump(line_dic, writefile)
                writefile.write('\n')
                wiki_file_size+=1
                print(json_file_size, '&',wiki_file_size, '...over')
    print('tokenize over')
    writefile.close()


def reformat_into_expected_ESA():
    '''
    super super slow. do not use it
    '''
    start_time = time.time()
    global Word2TileCount
    global WordTitle2Count
    route = '/home/wyin3/Datasets/Wikipedia20190320/parsed_output/statistics_from_json/'
    rows=[]
    cols=[]
    values =[]
    size = 0
    print('WordTitle2Count:', WordTitle2Count)
    for key, value in WordTitle2Count.items(): #"0:0": 8, "1:0": 24,
        key_parts = key.split(':')
        word_id_str = key_parts[0]
        concept_id_str = key_parts[1]
        word_df =Word2TileCount.get(word_id_str)
        rows.append(int(word_id_str))
        cols.append(int(concept_id_str))
        values.append(value/word_df)
        size+=1
        if size%10000000 ==0:
            print('reformat entry sizes:', size)
    WordTitle2Count=None # release the memory of big dictionary
    print('reformat entry over, building sparse matrix...')
    sparse_matrix = csr_matrix((values, (rows, cols)))
    non_zero=sparse_matrix.nonzero()
    row_array = list(non_zero[0])
    col_array = non_zero[1]
    print('sparse matrix build succeed, start store...')
    writefile = codecs.open(route+'ESA.v1.json', 'w', 'utf-8')
    prior_row = -1
    finish_size=0
    for id, row_id in enumerate(row_array):
        if row_id !=prior_row:
            if row_id>0:
                # print(prior_row.dtype)
                json.dump({str(prior_row):new_list}, writefile)
                writefile.write('\n')
                new_list=None
                finish_size+=1
                if finish_size %1000:
                    print('finish store rows ', finish_size)
            # else:
            new_list=[]
            new_list.append(str(col_array[id])+':'+str(sparse_matrix[row_id,col_array[id]]))
            prior_row=row_id
        else:
            new_list.append(str(col_array[id])+':'+str(sparse_matrix[row_id,col_array[id]]))

    json.dump({str(prior_row):new_list}, writefile) # the last row
    writefile.close()
    print('ESA format over')
    spend_time = (time.time()-start_time)/60.0
    print(spend_time, 'mins')

def reformat_into_sparse_matrix_store(data_dir):
    start_time = time.time()
    global Word2TileCount
    global WordTitle2Count
    route = '{}/0shot/BenchmarkingZeroShot/dataset/wikipedia/parsed_output/statistics_from_json'.format(data_dir)
    rows=[]
    cols=[]
    values =[]
    size = 0
    for key, value in WordTitle2Count.items(): #"0:0": 8, "1:0": 24,
        key_parts = key.split(':')
        word_id_str = key_parts[0]
        concept_id_str = key_parts[1]
        word_df =Word2TileCount.get(word_id_str)
        rows.append(int(word_id_str))
        cols.append(int(concept_id_str))
        values.append(value/word_df)
        size+=1
        if size%10000000 ==0:
            print('reformat entry sizes:', size)
    WordTitle2Count=None # release the memory of big dictionary
    print('reformat entry over, building sparse matrix...')
    sparse_matrix = csr_matrix((values, (rows, cols)))
    print('sparse matrix build succeed, start store...')
    sparse.save_npz(route+"ESA_Sparse_v1.npz", sparse_matrix)
    print('ESA sparse matrix stored over, congrats!!!')
    spend_time = (time.time()-start_time)/60.0
    print(spend_time, 'mins')

def divide_sparseMatrix_by_list_row_wise(mat, lis):
    # C=lil_matrix([[2,4,6], [5,10,15]])
    # print(C)
    # print(type(mat))
    # print(type(lis))
    D=np.asarray(list(lis))
    # print(mat.shape)
    r,c = mat.nonzero()
    rD_sp = csr_matrix(((1.0 / D)[r], (r, c)), shape=(mat.shape))
    out = mat.multiply(rD_sp)
    # print(r.shape)
    # print(c.shape)
    # print(type(mat.getnnz(axis=1)))
    # val = np.repeat(1.0/D, mat.getnnz(axis=1))
    # rD_sp = csr_matrix((val, (r,c)), shape=(mat.shape))
    # out = mat.multiply(rD_sp)
    return  out

def multiply_sparseMatrix_by_list_row_wise(mat, lis):
    # C=lil_matrix([[2,4,6], [5,10,15]])
    # print(C)
    D=np.asarray(list(lis))
    r,c = mat.nonzero()
    rD_sp = csr_matrix(((D)[r], (r, c)), shape=(mat.shape))
    out = mat.multiply(rD_sp)

    return  out

def load_sparse_matrix_4_cos(row1, row2):
    print('loading sparse matrix for cosine computation...')
    sparse_matrix = sparse.load_npz('/home/wyin3/Datasets/Wikipedia20190320/parsed_output/statistics_from_json/ESA_Sparse_v1.npz')
    print('cos: ', cosine_similarity(sparse_matrix.getrow(row1), sparse_matrix.getrow(row2)))


def crs_matrix_play():
    # mat = lil_matrix((3, 5))
    # mat[0,0]+=1
    # print(mat)
    # simi = cosine_similarity(mat.getrow(0), mat.getrow(0))
    # print(simi)
    # C=lil_matrix([[2,4,6], [5,10,15]])
    # print(C)
    # D=[2,5]
    # C=divide_sparseMatrix_by_list_row_wise(C,D)
    # print(C)

    C=lil_matrix([[2,4,6], [5,10,15], [1,10,9]])
    sub=C[[0,2],:]
    print(C)
    print('haha',sub)
    print(sub.sum(axis=0))


def get_wordsize_pagesize(data_dir):
    '''
    we first tokenzie tool output json files into a single json file "tokenized_wiki.txt"
    now we do statistics on it
    '''
    start_time = time.time()
    global title2id
    global word2id
    global title_size
    global word_size
    # global WordTitle2Count
    # global Word2TileCount
    # global fileset

    route = '{}/0shot/BenchmarkingZeroShot/dataset/wikipedia/parsed_output/tokenized_wiki/'.format(data_dir)
    wiki_file_size = 0
    with codecs.open(route+'tokenized_wiki.txt', 'r', 'utf-8') as f:
        for line in f:
            try:
                line_dic = json.loads(line)
            except ValueError:
                continue
            title = line_dic.get('title')
            title_id = title2id.get(title)
            if title_id is None: # if word was not in the vocabulary
                title_id=title_size  # id of true words starts from 1, leaving 0 to "pad id"
                title2id[title]=title_id
                title_size+=1

            # content = line_dic.get('text')
            tokenized_text = line_dic.get('text').split()
            word2tf=Counter(tokenized_text)
            for word, tf in word2tf.items():
                word_id = word2id.get(word)
                if word_id is None:
                    word_id = word_size
                    word2id[word]=word_id
                    word_size+=1
                # WordTitle2Count[word_id, title_id]=tf
                # Word2TileCount[word_id]+=1 #this word meets a new title
            wiki_file_size+=1
            if wiki_file_size%1000==0:
                print(wiki_file_size, '...over')
            # if wiki_file_size ==4000:
            #     break
    f.close()
    print('word size:', word_size, ' title size:', title_size)

def ESA_cosine(text, label_list,ESA_sparse_matrix, ESA_word2id):
    all_texts, all_word2DF = load_text(text, ESA_word2id)
    label_veclist = []
    labelname_idlist = transfer_wordlist_2_idlist_with_existing_word2id(label_list, ESA_word2id)
    # print("label id list", labelname_idlist)
    for i in range(len(label_list)):
        # labelname_idlist = labelnames[i]
        '''label rep is sum up all word ESA vectors'''
        label_veclist.append(text_idlist_2_ESAVector(ESA_sparse_matrix, labelname_idlist[i], False, all_word2DF))
    # print("label vec list", label_veclist)
    text_idlist = all_texts[0]
    # print("text id list", text_idlist)
    text_vec = text_idlist_2_ESAVector(ESA_sparse_matrix, text_idlist, True, all_word2DF)
    # print("text vec", text_vec)
    cos_array = cosine_similarity(text_vec, np.vstack(label_veclist))
    # print("cos list", cos_array)
    max_id = np.argmax(cos_array, axis=1)
    # print("max id", max_id)

    for idx, cos in enumerate(cos_array[0]):
        cos_array[0][idx] = round(cos * 100, 4 )
    # print(cos_array[0])
    return cos_array[0]

def text_idlist_2_ESAVector(ESA_sparse_matrix, idlist, text_bool, all_word2DF):
    # sub_matrix = ESA_sparse_matrix[idlist,:]
    # return  sub_matrix.mean(axis=0)
    # matrix_list = []
    # for id in idlist:
    #     matrix_list.append(ESA_sparse_matrix_2_dict.get(id))
    # stack_matrix = vstack(matrix_list)
    # return  stack_matrix.mean(axis=0)
    # print('idlist:', idlist)
    if text_bool:
        sub_matrix = ESA_sparse_matrix[idlist,:]
        # myvalues = list(itemgetter(*idlist)(all_word2DF))
        myvalues = [all_word2DF.get(id) for id in idlist]
        weighted_matrix = divide_sparseMatrix_by_list_row_wise(sub_matrix, myvalues)
        return  weighted_matrix.sum(axis=0)
    else: #label names
        sub_matrix = ESA_sparse_matrix[idlist,:]
        return  sub_matrix.sum(axis=0)

def load_text(text, ESA_word2id):
    all_texts = []
    all_word2DF = defaultdict(int)
    # text_wordlist = text.strip().lower().split()[:100]  # [:30]
    text_wordlist = nltk.word_tokenize(text)[:100]
    # print(text_wordlist)

    text_idlist = transfer_wordlist_2_idlist_with_existing_word2id(text_wordlist, ESA_word2id)
    if len(text_idlist) > 0:
        all_texts.append(text_idlist)
        idset = set(text_idlist)
        for iddd in idset:
            all_word2DF[iddd] += 1
    # print(all_texts, all_word2DF)
    return all_texts, all_word2DF

def transfer_wordlist_2_idlist_with_existing_word2id(token_list, ESA_word2id):
    '''
    From such as ['i', 'love', 'Munich'] to idlist [23, 129, 34], if maxlen is 5, then pad two zero in the left side, becoming [0, 0, 23, 129, 34]
    '''
    idlist=[]
    # print(ESA_word2id)
    for word in token_list:
        id=ESA_word2id.get(word)
        if id is not None: # if word was not in the vocabulary
            idlist.append(id)
        else:
            idlist.append(0)
    return idlist

def load_ESA_word2id(data_dir):
    global ESA_word2id
    # Change below word2id.json file path to your own path
    route = '{}/word2id.json'.format(data_dir)
    with open(route, 'r') as fp2:
        ESA_word2id = json.load(fp2)
    print('load ESA word2id succeed')
    return ESA_word2id

def load_ESA_sparse_matrix(data_dir):
    # print('loading sparse matrix for cosine computation...')
    # Change below sparse_maxtrx file path to your own path
    sparse_matrix = sparse.load_npz('{}/ESA_Sparse_v1.npz'.format(data_dir))
    print('load ESA sparse matrix succeed')
    return sparse_matrix

def main(data_dir):
    # scan_all_json_files('/export/home/Dataset/wikipedia/parsed_output/json/')
    '''note that file size 13354 does not mean wiki pages; each file contains multiple wiki pages'''
    # print('fileset size:', len(fileset)) #fileset size: 13354
    # load_json() #time-consuming, not useful
    # store_ESA()
    '''to save time, we tokenize wiki dump and save into files for future loading'''
    tokenize_filter_tokens(data_dir)
    '''word size 6161731; page size: 5903486'''
    get_wordsize_pagesize(data_dir)
    load_tokenized_json(data_dir)
    '''store all the statistic dictionary into files for future loading'''
    store_ESA(data_dir)
    # load_sparse_matrix_4_cos(1,2)

    # reformat_into_sparse_matrix_store()


if __name__ == '__main__':
    # ESA_sparse_matrix = load_ESA_sparse_matrix().tocsr()
    # print(ESA_sparse_matrix.shape)
    # word2id = load_ESA_word2id()
    # ESA_cosine("This is a test sentence.", ["happy", "sad", "health"], ESA_sparse_matrix, word2id)
    main()
    # parser = argparse.ArgumentParser()
    #
    # ## Required parameters
    # parser.add_argument("--data_dir",
    #                     default=None,
    #                     type=str,
    #                     # required=True,
    #                     help="The input data dir. Should contain the .tsv files (or other data files) for the task.")
    # args = parser.parse_args()
    # # scan_all_json_files('/export/home/Dataset/wikipedia/parsed_output/json/')
    # '''note that file size 13354 does not mean wiki pages; each file contains multiple wiki pages'''
    # # print('fileset size:', len(fileset)) #fileset size: 13354
    # # load_json() #time-consuming, not useful
    # # store_ESA()
    # '''to save time, we tokenize wiki dump and save into files for future loading'''
    # tokenize_filter_tokens(data_dir)
    # '''word size 6161731; page size: 5903486'''
    # get_wordsize_pagesize(data_dir)
    # load_tokenized_json(data_dir)
    # '''store all the statistic dictionary into files for future loading'''
    # store_ESA(data_dir)
    # # load_sparse_matrix_4_cos(1,2)
    #
    # # reformat_into_sparse_matrix_store()
