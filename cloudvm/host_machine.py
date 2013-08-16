class HostMachine:
	def kill_all(self, ctx):
		for container in ctx.docker.containers():
			ctx.info("killing " + container['Id'])
			ctx.docker.kill(container['Id'])

	def delete_exited(self, ctx):
		for container in ctx.docker.containers(all = True):
			details = ctx.docker.inspect_container(container['Id'])
			if not details['State']['Running']:
				ctx.info("removing " + container['Id'])
				ctx.docker.remove_container(container['Id'])

	def delete_images(self, ctx):
		for image in ctx.docker.images():
			ctx.info("removing " + image['Id'])
			ctx.docker.remove_image(image['Id'])

	def to_json(self):
		return {
			"update_url" : "/host-machine/update",
			"kill_all_url" : "/host-machine/kill-all",
			"delete_exited" : "/host-machine/delete-exited",
			"delete_images" : "/host-machine/delete-images"
		}


