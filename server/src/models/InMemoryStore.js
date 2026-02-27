// Simple in-memory clip storage for development/testing
let clips = [];
let idCounter = 1;

class InMemoryClip {
  constructor(data) {
    this._id = idCounter++;
    this.fileName = data.fileName;
    this.url = data.url;
    this.hypeScore = data.hypeScore;
    this.triggerType = data.triggerType;
    this.createdAt = data.createdAt || new Date();
  }

  async save() {
    clips.push(this);
    return this;
  }

  static async find() {
    return clips.sort((a, b) => b.createdAt - a.createdAt);
  }

  static async findById(id) {
    return clips.find(clip => clip._id === parseInt(id));
  }

  static async findByIdAndDelete(id) {
    const index = clips.findIndex(clip => clip._id === parseInt(id));
    if (index > -1) {
      return clips.splice(index, 1)[0];
    }
    return null;
  }
}

module.exports = {
  InMemoryClip,
  clearClips: () => { clips = []; idCounter = 1; }
};
