from pathlib import Path

from flask import Flask, jsonify, make_response
from flask_restful import Api, Resource, reqparse

from mutcompute.scripts.run import fetch_pdb_file
from task import run_mutcompute

nn_app = Flask(__name__)
nn_api = Api(nn_app)


class InferenceAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        # Makes sure pdb_code is passed in when calling this api endpoint. it can come either through form or json. 
        # This requirement is only enforced when a POST request is sent. 
        self.reqparse.add_argument('pdb_code', type=str, required=True, location=['json'], help='No pdb_code provided.', )
        self.reqparse.add_argument('username', type=str, required=True, location=['json'], help='No username/email address provided.', )
        self.reqparse.add_argument('load_cache', type=bool, required=False, location=['json'], help='Whether to load predictions of an already ran protein.', )
        
        super().__init__()

    def get(self):
        return jsonify(Result='Ready to accept PDB codes.')

    def post(self):
        args = self.reqparse.parse_args()   # This will parse arguments passed in through a form or json.

        pdb_code    = args.get('pdb_code').upper().strip()
        email       = args.get('username').strip()
        load_cache  = args.get('load_cache', False)

        print("Email:", email)
        print("PDB code:", pdb_code)
        print("Load cached protein: ", load_cache)

        if "@" in email and len(pdb_code) == 4:
            try:
                if load_cache:
                    pdb_file = Path('/mutcompute_2020/mutcompute/data/pdb_files') / f'{pdb_code}.pdb'

                else:
                    pdb_file = fetch_pdb_file(pdb_code, dir='/mutcompute_2020/mutcompute/data/pdb_files')

                    print(f'Created PDB file: ', pdb_file)
                    
            except Exception:
                return make_response(
                    jsonify(
                        Result=f'Unabled to retrieve PDB file for {pdb_code.upper()} from the PDB-REDO or the RCSB servers'
                    ), 
                    400
                )

            else:
                run_mutcompute.delay(email, pdb_file.name, fs_pdb=True, load_cache=load_cache,
                    dir='/mutcompute_2020/mutcompute/data/pdb_files', out_dir='/mutcompute_2020/mutcompute/data/inference_CSVs', )
                
                return make_response(
                    jsonify(Result=f"""
                        Neural Net is running PDB file: {pdb_code.upper()}. 
                        Expect an email with predictions within a few minutes or up to an hour. 
                        Larger proteins tend to take longer.
                    """), 
                    201
                ) 
        else:
            return make_response(
                    jsonify(Result=f'Error in parsing arguments: {pdb_code.upper()} {email}'), 
                    422
                ) 



nn_api.add_resource(InferenceAPI, '/inference', endpoint='nn_query')


if __name__=='__main__':
    nn_app.run(host='0.0.0.0', port=8000, debug=True)
