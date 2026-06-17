from flask import Flask, render_template, request, jsonify

from db import Repository


def create_app(repository: Repository) -> Flask:
    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template('index.html')

    # @app.route('/crawler/start', methods=['POST'])
    # def start_crawler():
    #     if not repository.try_start_crawler():
    #         return jsonify({"status": "already_running"}), 409
    #     return jsonify({"status": "started"})
    #
    # @app.route('/crawler/stop', methods=['POST'])
    # def stop_crawler():
    #     repository.stop_crawler()
    #     return jsonify({"status": "stopping"})

    @app.route('/crawler/status', methods=['GET'])
    def status_crawler():
        running = repository.is_crawler_running()
        return jsonify({"running": running})

    @app.route('/api/artists', methods=['POST'])
    def get_artists():
        data = request.get_json()

        filters = data.get('filters', {})

        page = data.get('page', 1)
        page_size = data.get('pageSize', 20)
        sort_by = data.get('sortBy', 'name')
        sort_order = data.get('sortOrder', 'asc')

        artists_page = repository.get_artists_page(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters
        )

        return jsonify(artists_page.to_dict())

    return app
