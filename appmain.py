from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def main():
    return render_template('main1.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/mock')
def moc():
    return render_template('moc1.html')

@app.route('/resume')
def resume():
    return render_template('res.html')

@app.route('/aptitude')
def aptitude():
    return render_template('aptitude.html')

@app.route('/editor')
def editor():
    return render_template('editor.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000)