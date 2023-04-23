# Loading Chainmeta Files
When loading a chainmeta file, chainmeta_reader uses the artifact schema specified in the file to locate the corresponding translator and validator. This happens automatically, and all you need to do is to complete implementing the placeholder files generated by the `make new-contributor` command in the `chainmeta_reader/contrib` folder.

The translator is responsible for converting the chainmeta between the common schema and the custom schema defined by the participant. The validator is responsible for validating the chainmeta against the custom schema. These files should be completed by the participant to ensure that their metadata can be properly loaded and validated by chainmeta_reader.

Once you have completed these files, chainmeta_reader will automatically use them when loading chainmeta files with the specified artifact schema. This allows for seamless integration of participant-defined custom schemas into the Open Chainmeta project.

Below example shows how a chainmeta file is associated with the chaintool's translator and validator
![image](https://user-images.githubusercontent.com/488359/232187925-faf7aa7a-7848-46bc-bd26-d63ec0921941.png)