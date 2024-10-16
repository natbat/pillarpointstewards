class ImageUploader extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <style>
                #upload-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 10px;
                    padding-bottom: 1em;
                }
                #thumbnail {
                    max-width: 200px;
                    max-height: 200px;
                }
                #progress-bar {
                    width: 0%;
                    height: 20px;
                    background-color: green;
                }
                #progress-container {
                    width: 100%;
                    background-color: #ddd;
                }
            </style>
            <div id="upload-container">
                <input type="file" id="file-input" accept="image/*" hidden>
                <label for="file-input" id="file-input-label">Add a photo</label>
                <img id="thumbnail" src="" hidden>
                <button id="upload-button" hidden>Upload photo</button>
                <div id="progress-container" hidden>
                    <div id="progress-bar"></div>
                </div>
                <div id="upload-complete" hidden>
                    Upload complete! <button id="select-another">Select another photo</button>
                </div>
            </div>
        `;

        this.fileInput = this.shadowRoot.getElementById('file-input');
        this.thumbnail = this.shadowRoot.getElementById('thumbnail');
        this.uploadButton = this.shadowRoot.getElementById('upload-button');
        this.progressBarContainer = this.shadowRoot.getElementById('progress-container');
        this.progressBar = this.shadowRoot.getElementById('progress-bar');
        this.uploadCompleteMessage = this.shadowRoot.getElementById('upload-complete');
        this.selectAnotherButton = this.shadowRoot.getElementById('select-another');

        this.fileInput.addEventListener('change', () => this.handleFileSelection());
        this.uploadButton.addEventListener('click', () => this.uploadImage());
        this.selectAnotherButton.addEventListener('click', () => this.resetUploader());
    }

    connectedCallback() {
        if (this.hasAttribute('text')) {
            const text = this.getAttribute('text');
            this.shadowRoot.querySelector('#file-input-label').textContent = text;
        }
    }

    handleFileSelection() {
        const file = this.fileInput.files[0];
        if (file) {
            this.thumbnail.src = URL.createObjectURL(file);
            this.thumbnail.hidden = false;
            this.uploadButton.hidden = false;
        }
    }

    async uploadImage() {
        const file = this.fileInput.files[0];
        if (!file) {
            return;
        }

        // Upload original image
        const originalKey = await this.uploadFile(file);

        // Create and upload thumbnail
        const thumbnailBlob = await this.createThumbnail(file);
        const thumbnailKey = await this.uploadFile(thumbnailBlob, true);

        this.uploadComplete(originalKey, thumbnailKey);
    }

    async uploadFile(file, isThumb = false) {
        const contentType = isThumb ? 'image/jpeg' : file.type;
        const response = await fetch(
            `/photo-upload-credentials/?content_type=${encodeURIComponent(contentType)}${isThumb ? '&thumb=1' : ''}`
        );
        const s3Params = await response.json();

        const formData = new FormData();
        for (const [key, value] of Object.entries(s3Params.fields)) {
            formData.append(key, value);
        }
        formData.append('file', file);

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', s3Params.url, true);

            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const progress = (event.loaded / event.total) * 100;
                    this.progressBar.style.width = progress + '%';
                }
            });

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(s3Params.fields.key);
                } else {
                    reject(new Error('Upload failed: ' + xhr.responseText));
                }
            };

            this.progressBarContainer.hidden = false;
            xhr.send(formData);
        });
    }

    async createThumbnail(file) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = 150;
                canvas.height = 150;

                const size = Math.min(img.width, img.height);
                const x = (img.width - size) / 2;
                const y = (img.height - size) / 2;

                ctx.drawImage(img, x, y, size, size, 0, 0, 150, 150);

                canvas.toBlob((blob) => {
                    resolve(blob);
                }, 'image/jpeg', 0.95);
            };
            img.src = URL.createObjectURL(file);
        });
    }

    async uploadComplete(originalKey, thumbnailKey) {
        this.thumbnail.hidden = true;
        this.uploadButton.hidden = true;
        this.progressBarContainer.hidden = true;
        this.uploadCompleteMessage.hidden = false;

        const formData = new URLSearchParams();
        formData.append('key', originalKey);
        formData.append('thumbnail_key', thumbnailKey);
        formData.append('shift_id', this.getAttribute('shift-id'));
        formData.append('is_profile_photo', this.getAttribute('is-profile-photo'));

        await fetch('/photo-upload-complete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getAttribute('csrf-token'),
            },
            body: formData.toString()
        });

        this.dispatchEvent(new CustomEvent('upload-complete', { 
            detail: { originalKey, thumbnailKey } 
        }));
    }

    resetUploader() {
        this.fileInput.value = '';
        this.thumbnail.hidden = true;
        this.uploadButton.hidden = true;
        this.progressBarContainer.hidden = true;
        this.uploadCompleteMessage.hidden = true;
    }
}

customElements.define('image-uploader', ImageUploader);