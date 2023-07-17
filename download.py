import os
import re
from git import Repo
import json

use_existing_repo = True

# Specify the URL of the Git repository and the local directory to clone it to
repo_url = 'https://github.com/woocommerce/woocommerce.git'
local_dir = './repository'
results_dir = './templates'

template_version_regex = re.compile(r"\* @version\s+(.*)")

# Clone the Git repository
if not use_existing_repo:
  print('Cloning repository')
  Repo.clone_from(repo_url, local_dir)

# Open the cloned repository
repo = Repo(local_dir)
repo.config_writer().set_value("core", "protectNTFS ", "false").release()

templates_found = []

meta = {}

versions = ['7.8.0', '7.7.0', '7.6.0', '7.5.0', '7.4.0', '7.3.0', '7.2.0', '7.1.0', '7.0.0', '6.9.0', '6.8.0', '6.7.0', '6.6.0', '6.5.0', '6.4.0', '6.3.0', '6.2.0', '6.1.0', '6.0.0', '5.9.0', '5.8.0', '5.7.0', '5.6.0', '5.5.0', '5.4.0', '5.3.0', '5.2.0', '5.1.0', '5.0.0', '4.9.0', '4.8.0', '4.7.0', '4.6.0', '4.5.0', '4.4.0', '4.3.0', '4.2.0', '4.1.0', '4.0.0', '3.9.0', '3.8.0', '3.7.0', '3.6.0', '3.5.0', '3.4.0', '3.3.0', '3.2.0', '3.1.0', '3.0.0', '2.6.0']
# versions = ['7.8.0', '7.4.0', '4.4.0'] # Debugging

# Iterate over the specified tags
for tag in versions:
    # remove v from tag
    tag_name = tag
    major_version = int(tag_name.split('.')[0])
    template_location = 'plugins/woocommerce/templates/' if major_version >= 6 else 'templates/'

    # Checkout the tag to get the files
    try:  
      print('Downloading files from tag {}'.format(tag_name))
      repo.git.checkout(tag)
    except:
      print('Failed to checkout tag {}. Skipping...'.format(tag_name))
      continue

    template_tag_search = '* @version {}'.format(tag_name)

    # Copy the files from the repository to the tag folder
    for file in repo.tree().traverse():
        if file.type == 'blob' and file.path.startswith(template_location):
            try:
              file_content = repo.git.show('{}:{}'.format(tag_name, file.path))
            except:
              print('Failed to get file content for file {}. Skipping...'.format(file.path))
              continue
            
            # Skip if version is not current tag. This means the file is not updated in this version. 
            matches = template_version_regex.search(file_content)
            if not matches:
              continue

            version = matches.group(1)

            original_template_path = file.path.replace(template_location, '')
            file_name = original_template_path.replace('.php', '.php/{}.php'.format(version))

            # Check template already found
            if file_name in templates_found:
              continue

            templates_found.append(file_name)

            file_path = os.path.join(results_dir, file_name)
            
            # Create the folder if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Add version to meta
            if original_template_path not in meta:
              meta[original_template_path] = { 'versions': [] }

            meta[original_template_path]['versions'].append(version)

            # TODO: Add to metadata if template is deleted on a later version
            
            with open(file_path, 'wb') as f:
                print('Writing file {}'.format(file_path))
                f.write(file_content.encode())


# Write meta file
with open('./meta.json', 'w') as f:
  print('Writing meta file')
  f.write(json.dumps({ 
    'versions': versions.reverse(), 
    'templates': meta 
  }))

print('Done')