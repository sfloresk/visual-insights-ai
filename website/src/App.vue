<!--
     Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
   
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
-->
<script setup>
import Header from './components/AppHeader.vue'
import Footer from './components/AppFooter.vue'
import '@aws-amplify/ui-vue/styles.css';
import { Authenticator } from '@aws-amplify/ui-vue';
import { fetchAuthSession } from 'aws-amplify/auth';
import {ListBucketsCommand, S3Client} from "@aws-sdk/client-s3";
import {fromCognitoIdentityPool} from "@aws-sdk/credential-providers";
</script>

<template>
  <div style="margin-top:80px"></div>
  <authenticator v-slot="{ user, signOut }">
    <div class="container py-4 px-3 mx-auto">
      <Header @cognitoSignOut="signOut" />
      <div style="margin-top:20px">
      </div>


      <ul class="nav nav-tabs">
        <li class="nav-item">
          <a :class="{ active: selectedTab == 'imageProcessing' }" class="nav-link" aria-current="page" href="#"
            @click="changeTab('imageProcessing')">Image processing</a>
        </li>
        <li class="nav-item">
          <a :class="{ active: selectedTab == 'history' }" class="nav-link" href="#"
            @click="changeTab('history')">History for {{ user.signInDetails.loginId }}</a>
        </li>
      </ul>
      <div style="margin-top:20px">
      </div>

      <!-- ITEM RECOGNITION -->
      <div class="container-fluid marketing" v-if="selectedTab == 'imageProcessing'">

        <div class="row featurette">
          <div class="col-md-12">
            <p class="lead"><b>This is shared demo environment - do not upload confidential information</b></p>
            <p class="lead">Take or upload a picture of items in your pantry cabinet to start the processing</p>
          </div>
        </div>
        <div class="row row-cols-1 row-cols-md-3 mb-4">
          <div class="col-md-3">
            <img id="selectedImg" v-if=currentImage v-bind:src=currentImage data-bs-toggle="modal"
              data-bs-target="#imageModal" style="cursor: pointer"
              class="img-fluid border rounded-3 shadow-lg mb-4 img-thumbnail" loading="lazy">

            <label v-if="!isItemFromImageLoading" for="cameraFileInput">
              <span v-if="!currentImage" class="btn btn-secondary btn-block mt-3">Add image</span>
              <span v-if="currentImage" class="btn btn-secondary btn-block mt-3">Change image</span>


              <!-- The hidden file `input` for opening the native camera -->
              <input @change="checkInputImage" style="display: none;" id="cameraFileInput" type="file"
                accept="image/*" />
            </label>

            <!-- Image modal -->
            <div class="modal fade" id="imageModal" tabindex="-1" aria-labelledby="imageModalLabel" aria-hidden="true">
              <div class="modal-dialog" style="max-width : 1300px;">
                <div class="modal-content">
                  <div class="modal-body">
                    <img id="selectedImg" v-if=currentImage v-bind:src=currentImage class="img-fluid">
                  </div>
                </div>
              </div>
            </div>
            <!---->
          </div>
        </div>
        
        <div class="row row-cols-3 row-cols-md-3 mb-4 text-center">
          <div class="col-md-12">
            <button v-if="!isImageProcessingLoading" class="btn btn-success btn-block mt-3"
              @click="processImage">Process
              image</button>
            <p v-if="isImageProcessingLoading" style="text-align: center;">
            <div class="text-center">
              <div class="spinner-border text-warning" role="status">
              </div>
              <p>Reading image...</p>
            </div>
            </p>
          </div>
          <!-- Response modal -->
          <a href="#" ref="responseModalLink" style="display: none;" data-bs-toggle="modal"
            data-bs-target="#responseModal">See results</a>
          <div class="modal fade" id="responseModal" tabindex="-1" aria-labelledby="responseModalLabel"
            aria-hidden="true">
            <div class="modal-dialog" style="max-width:1300px">
              <div class="modal-content">
                <div class="modal-header">
                  <h1 class="modal-title fs-5" id="responseModalLabel">Response</h1>
                  <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                  <pre style="white-space: pre-wrap;text-align: left;">{{ imageProcessingResponse }}</pre>
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
              </div>
            </div>
          </div>
          <!---->
        </div>
      </div>
      <!-- History -->
      <div class="container-fluid marketing" v-if="selectedTab == 'history'">
        <div class="row row-cols-2 row-cols-md-3 mb-4 text-end">
          <div class="col-md-11">
            <input type="text" placeholder="Search items by name" v-model="resultSearch" class="form-control" />
          </div>
          <div class="col-md-1">
            <button v-if="!isImageProcessingLoading" class="btn btn-secondary btn-block"
              @click="getResultList">Refresh</button></div>
        </div>
        <div class="row featurette">
          <div class="col-md-12">
            <table class="table">
              <thead>
                <tr>
                  <th scope="col">Date</th>
                  <th scope="col">Filename</th>
                  <th scope="col">Image</th>
                  <th scope="col">Result</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in filteredResults">
                  <th>{{ item.date }}</th>
                  <th>{{ item.fileName }}</th>
                  <td>
                    <img v-bind:src=item.presignedUrl class="img-fluid border rounded-3 shadow-lg mb-2 img-thumbnail"
                      style="max-width: 200px; cursor: pointer" data-bs-toggle="modal"
                      v-bind:data-bs-target="'#' + item.fileName.replace(/ /g, '').replace(/\./g, '').replace(/-/g, '')" />
                    <!-- Image modal -->
                    <div class="modal fade"
                      v-bind:id="item.fileName.replace(/ /g, '').replace(/\./g, '').replace(/-/g, '')" tabindex="-1"
                      aria-labelledby="imageModalLabel" aria-hidden="true">
                      <div class="modal-dialog" style="max-width : 1300px;">
                        <div class="modal-content">
                          <div class="modal-body">
                            <img v-bind:src=item.presignedUrl
                              class="img-fluid border rounded-3 shadow-lg mb-2 img-thumbnail" />
                          </div>
                        </div>
                      </div>
                    </div>
                    <!---->
                  
                  </td>
                  <td><pre style="white-space: pre-wrap;text-align: left;">{{ JSON.stringify(item.result, undefined, 2) }}</pre></td>
                </tr>
              </tbody>
            </table>

          </div>
        </div>
      </div>

      <hr />
      <Footer />
    </div>
  </authenticator>
</template>
<script>
export default {
  name: 'App',
  mounted() {
    this.getResultList();
  },
  
  data: function () {
    return {
      selectedTab: 'imageProcessing',
      prompt: "",
      loadingImageMessage: null,
      currentImage: null,
      currentFile: null,
      isImageProcessingLoading: false,
      isResultListProcessing: false,
      imageProcessingResponse: {},
      results: [],
      resultSearch: ''
    }
  },
  computed: {
    filteredResults() {
      return this.results.filter(item => {
         return item.fileName.toLowerCase().indexOf(this.resultSearch.toLowerCase()) > -1
      })
    }
  },
  methods: {
    getResultList() {
      this.isResultListProcessing = true
      // Setting credentials
      async function currentSession() {
        try {
          const { accessToken, idToken } = (await fetchAuthSession()).tokens ?? {};
          return idToken.toString();
        } catch (err) {
          console.log(err);
          this.errorMessage = "Invalid token, please sign in again"
        }
      }
      currentSession().then(idToken => {
        fetch("https://CHANGE_ME/dev/images/result", {
          "method": "GET",
          "headers": {
            "Authorization": idToken
          }
        }).then(response => {
          if (response.ok) {
            return response.json()
          } else {
            console.log("Server returned " + response.status + " : " + response.statusText);
          }
        }).then(response => {
          console.log(response)
          this.results = response
        }).catch(err => {
          console.log(err);
          this.errorMessage = err + " Check your internet connection or sign in again"
          this.isResultListProcessing = false
        });
      });
    },
    setPrompt(pPrompt) {
      this.prompt = pPrompt;
    },
    checkInputImage(event) {
      this.currentImage = window.URL.createObjectURL(event.target.files[0])
      this.currentFile = event.target.files[0]

    },
    changeTab(event) {
      // Change UI tabs
      console.log("Captured event " + event)
      this.selectedTab = event
    },
    processImage() {
      this.isImageProcessingLoading = true
      console.log("Processing image")
      var reader = new FileReader();
      reader.readAsDataURL(this.currentFile);
      let vueContext = this
      reader.onload = function () {
        let currentImageBase64 = reader.result.split(",")[1];
        console.log("Sending new image...")
        let body
        body = JSON.stringify({
          "file_content": currentImageBase64,
          "file_name": vueContext.currentFile.name,
          "metadata": vueContext.prompt
        })
        console.log({
          body
        })
        currentSession().then(idToken => {
          fetch("https://CHANGE_ME/dev/images/read", {
            "method": "POST",
            "body": body,
            "headers": {
              "Authorization": idToken
            }
          }).then(response => {
            if (response.ok) {
              return response.json()
            } else {
              console.log("Server returned " + response.status + " : " + response.statusText);
            }
          }).then(response => {
            console.log(response)
            vueContext.isImageProcessingLoading = false
            vueContext.imageProcessingResponse = response
            console.log(vueContext.$refs.responseModalLink)
            vueContext.$refs.responseModalLink.click()
            vueContext.getResultList()

          }).catch(err => {
            console.log(err);
            vueContext.errorMessage = err + " Check your internet connection or sign in again"
            vueContext.isImageProcessingLoading = false
          });
        });
      }
      reader.onerror = function (error) {
        console.log('Error: ', error);
      };
    }
  },
  watch: {
  }
}

// Retrieve credentials
async function currentSession() {
  try {
    const { accessToken, idToken } = (await fetchAuthSession()).tokens ?? {};
    return idToken.toString();
  } catch (err) {
    console.log(err);
    this.errorMessage = "Invalid token, please sign in again"
  }
}
</script>