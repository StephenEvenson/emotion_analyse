from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from nlp.danmu import assess_comment, assess_all_comment, judge_url_type, single_video_wf, space_video_wf, \
    single_video_dg, space_video_dg

app = Flask(__name__)
api = Api(app)


def resp(data=''):
    STATS = {
        'code': 200,
        'message': 'success',
        'data': data,
    }

    return STATS


def abort_if_video_doesnt_exist(bullet_screen_id):
    if bullet_screen_id is False:
        abort(404, message="视频不见了哟")


def abort_if_url_doesnt_exist(url_type):
    if url_type == 0:
        abort(404, message="输入的链接不正确")


parser = reqparse.RequestParser()
parser.add_argument('url')
parser.add_argument('num', type=int)


# class TabrResource(Resource):
#     def options(self):
#         return {'Allow': '*'}, 200, {'Access-Control-Allow-Origin': '*',
#                                      'Access-Control-Allow-Methods': 'HEAD, OPTIONS, GET, POST, DELETE, PUT',
#                                      'Access-Control-Allow-Headers': 'Content-Type, Content-Length, Authorization, '
#                                                                      'Accept, X-Requested-With , yourHeaderFeild',
#                                      }


class BulletScreen(Resource):
    def post(self):
        args = parser.parse_args()
        url = args['url']
        num = args['num']
        url_type = judge_url_type(url=url)
        abort_if_url_doesnt_exist(url_type)
        if url_type == 1:
            bullet_screen_id = assess_comment(url)
        elif url_type == 2:
            bullet_screen_id = assess_all_comment(url, num)  # bullet_screen_id是is_exist
        abort_if_video_doesnt_exist(bullet_screen_id)
        return resp()


class WordFrequency(Resource):
    def post(self):
        args = parser.parse_args()
        url = args['url']
        url_type = judge_url_type(url=url)
        abort_if_url_doesnt_exist(url_type)
        if url_type == 1:
            base = single_video_wf(url)
        elif url_type == 2:
            base = space_video_wf(url)
        return resp(base)


class Diagram(Resource):
    def post(self):
        args = parser.parse_args()
        url = args['url']
        num = args['num']
        url_type = judge_url_type(url=url)
        abort_if_url_doesnt_exist(url_type)
        if url_type == 1:
            if num is not None:
                base = single_video_dg(url, n=num)
            else:
                base = single_video_dg(url)
        elif url_type == 2:
            if num is not None:
                base = space_video_dg(url, n=num)
            else:
                base = space_video_dg(url)
        return resp(base)


api.add_resource(BulletScreen, '/bilibili/bullet_screen/')
api.add_resource(WordFrequency, '/bilibili/word_fq/')
api.add_resource(Diagram, '/bilibili/diagram/')

if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)

# flask run -h 0.0.0.0 -p 8001
# python app.py
