import asyncio
import os
import pygit2
import concurrent.futures

async def download_repo(repo_url, target_dir):
    # Clone the repository
    repo = pygit2.clone_repository(repo_url, target_dir)

    # Get the list of files in the repository
    files = repo.listall_files()

    # Filter the list to include only package.json files
    package_files = [file for file in files if file.endswith('package.json')]

    # Download the package files
    for file in package_files:
        # Read the contents of the file
        file_contents = repo.get(file).read_raw().decode('utf-8')

        # Parse the package.json file
        package_json = json.loads(file_contents)

        # Save the package.json file to a new folder
        output_dir = os.path.join(target_dir, '_sort')
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, file), 'w') as f:
            json.dump(package_json, f, indent=4)

async def delete_repo(repo_url, target_dir):
    # Delete the repository
    shutil.rmtree(target_dir)

async def main():
    # List of GitHub repositories to download and search in
    repo_urls = [
        'https://github.com/example/example-repo.git',
        'https://github.com/example/example-repo2.git',
        'https://github.com/example/example-repo3.git',
    ]

    # Download the repositories concurrently using 25 threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        tasks = [executor.submit(download_repo, repo_url, os.path.join('repos', repo_url.split('/')[-1].replace('.git', ''))) for repo_url in repo_urls]
        for task in concurrent.futures.as_completed(tasks):
            await task

    # Delete the repositories concurrently using 25 threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        tasks = [executor.submit(delete_repo, repo_url, os.path.join('repos', repo_url.split('/')[-1].replace('.git', ''))) for repo_url in repo_urls]
        for task in concurrent.futures.as_completed(tasks):
            await task

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()