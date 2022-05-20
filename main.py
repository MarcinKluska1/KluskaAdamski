import os
from flask import Flask, send_file
from flasgger import Swagger,  LazyJSONEncoder
from flask_restx import Api, Resource
from werkzeug.datastructures import FileStorage
from person_detection import get_results
from detection import video_detection

app = Flask(__name__)
api = Api(app)
app.json_encoder = LazyJSONEncoder

upload_parser = api.parser()
upload_parser.add_argument('file',
                           location='files',
                           type=FileStorage)

ns = api.namespace('Przetwarzanie', description='Dzień dobry wszystkim tu zgromadzonym')

swagger = Swagger(app)

@ns.route('/zdjecia/')
@ns.expect(upload_parser)
class UploadPicture(Resource):
    def post(self):
        """
        Przetwarzanie zdjęć
        """
        args = upload_parser.parse_args()
        file = args.get('file')
        file.save(os.path.join('uploads/', file.filename))
        get_results('uploads/'+file.filename)
        return send_file('processed_images/'+file.filename, as_attachment=True)

@ns.route('/wideo/')
@ns.expect(upload_parser)
class UploadVideo(Resource):
    def post(self):
        """
        Przetwarzanie wideo
        """
        args = upload_parser.parse_args()
        file = args.get('file')
        file.save(os.path.join('upload_videos/', file.filename))
        video_detection('upload_videos/'+file.filename, file.filename)
        return send_file('outputs/'+file.filename, as_attachment=True)


if __name__ == '__main__':
    port = os.environ.get("PORT", 5000)
    app.run(debug=False, host ="0.0.0.0", port=port)