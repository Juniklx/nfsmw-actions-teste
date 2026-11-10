// PRE671H: C++ host-only REAL Vulkan PFN ABI with mock callbacks.
// No Vulkan instance, device, query pool, application, APK, or GPU created.
#include "pre671_vk_separate_timestamp_pool_compile_only.h"
#include <cassert>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>
using namespace nfsmw::pre671;
namespace {
int creates=0,destroys=0,resets=0,writes=0,reads=0,idles=0;
VkResult create_result=VK_SUCCESS, read_result=VK_SUCCESS, idle_result=VK_SUCCESS;
bool avail=true;
std::vector<uint32_t> write_indices;
std::vector<VkPipelineStageFlagBits> write_stages;
VkQueryPool fake_pool(){
 static_assert(sizeof(VkQueryPool)==sizeof(uintptr_t), "mock handles need pointer width");
 VkQueryPool p=VK_NULL_HANDLE;
 const uintptr_t a=0x1100; std::memcpy(&p,&a,sizeof(p));return p;
}
VkDevice fake_device(){ return reinterpret_cast<VkDevice>(uintptr_t(0x2000)); }
VkCommandBuffer fake_cmd(){ return reinterpret_cast<VkCommandBuffer>(uintptr_t(0x3000)); }
VKAPI_ATTR VkResult VKAPI_CALL mock_create(VkDevice device,
  const VkQueryPoolCreateInfo* p,const VkAllocationCallbacks*,VkQueryPool* pool){
 ++creates;assert(device==fake_device());
 assert(p && p->sType==VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO);
 assert(p->queryType==VK_QUERY_TYPE_TIMESTAMP && p->queryCount==16);
 if(create_result!=VK_SUCCESS)return create_result;
 *pool=fake_pool();return VK_SUCCESS;
}
VKAPI_ATTR void VKAPI_CALL mock_destroy(VkDevice device,VkQueryPool pool,const VkAllocationCallbacks*){
 assert(device==fake_device()&&pool==fake_pool());++destroys;
}
VKAPI_ATTR void VKAPI_CALL mock_reset(VkCommandBuffer cmd,VkQueryPool pool,uint32_t start,uint32_t count){
 assert(cmd==fake_cmd() && pool==fake_pool());
 assert(count==8 && start<16 && start%8==0);++resets;
}
VKAPI_ATTR void VKAPI_CALL mock_write(VkCommandBuffer cmd,VkPipelineStageFlagBits stage,
 VkQueryPool pool,uint32_t at){
 assert(cmd==fake_cmd()&&pool==fake_pool()&&at<16);
 assert(stage==VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT||stage==VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
 ++writes;write_indices.push_back(at);write_stages.push_back(stage);
}
VKAPI_ATTR VkResult VKAPI_CALL mock_read(VkDevice device,VkQueryPool pool,
 uint32_t first,uint32_t count,size_t sz,void* data,VkDeviceSize stride,VkQueryResultFlags flags){
 assert(device==fake_device()&&pool==fake_pool() && first<16 && count<=8 && first+count<=16);
 assert(sz==count*2*sizeof(uint64_t) && stride==2*sizeof(uint64_t));
 assert(flags==(VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WITH_AVAILABILITY_BIT));
 ++reads;
 if(read_result!=VK_SUCCESS)return read_result;
 uint64_t* q=static_cast<uint64_t*>(data);
 for(uint32_t i=0;i<count;i++){q[2*i]=100+uint64_t(i)*5;q[2*i+1]=avail?1u:0u;}
 return VK_SUCCESS;
}
VKAPI_ATTR VkResult VKAPI_CALL mock_idle(VkDevice device){
 assert(device==fake_device());++idles;return idle_result;
}
Functions api(){
 Functions f;f.create=mock_create;f.destroy=mock_destroy;f.reset=mock_reset;
 f.write=mock_write;f.results=mock_read;f.device_wait_idle=mock_idle;return f;
}
}
int main(){
 static_assert(!kDefaultEnabled && kQueriesPerSlot==8 && kMaxPairsPerSlot==4);
 Adapter a;Samples out{};Functions f=api();
 assert(!a.Enabled() && a.QueryCount()==0);
 assert(!a.Create(fake_device(),f,false,2,32,2.5f));
 assert(!a.Create(fake_device(),f,true,2,0,2.5f));
 assert(!a.Create(fake_device(),f,true,17,32,2.5f));
 assert(!a.Create(fake_device(),f,true,2,32,0.0f));
 f.results=nullptr;assert(!a.Create(fake_device(),f,true,2,32,2.5f));f=api();
 assert(creates==0);
 create_result=VK_ERROR_OUT_OF_DEVICE_MEMORY;
 assert(!a.Create(fake_device(),f,true,2,32,2.5f));
 assert(creates==1);
 create_result=VK_SUCCESS;
 assert(a.Create(fake_device(),f,true,2,32,2.5f));
 assert(creates==2 && a.Enabled() && a.QueryCount()==16);
 assert(!a.Create(fake_device(),f,true,2,32,2.5f));
 assert(!a.BeginSlot(0,fake_cmd(),VK_NOT_READY));
 assert(!a.BeginSlot(0,fake_cmd(),VK_ERROR_DEVICE_LOST));
 assert(a.BeginSlot(0,fake_cmd(),VK_SUCCESS) && resets==1);
 assert(!a.BeginSlot(0,fake_cmd(),VK_SUCCESS));
 assert(!a.EndPair(0,fake_cmd()));
 assert(a.BeginPair(0,fake_cmd()) && writes==1);
 assert(!a.BeginPair(0,fake_cmd()));
 assert(!a.Submitted(0,VK_SUCCESS)); // cannot submit with open pair
 assert(a.EndPair(0,fake_cmd()) && writes==2);
 assert(write_indices[0]==0 && write_indices[1]==1);
 assert(write_stages[0]==VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT);
 assert(write_stages[1]==VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
 assert(a.Submitted(0,VK_SUCCESS));
 assert(!a.BeginSlot(0,fake_cmd(),VK_SUCCESS));
 assert(!a.ReadAfterFence(0,VK_NOT_READY,out) && reads==0);
 read_result=VK_NOT_READY;
 assert(!a.ReadAfterFence(0,VK_SUCCESS,out) && reads==1);
 read_result=VK_SUCCESS;avail=false;
 assert(!a.ReadAfterFence(0,VK_SUCCESS,out) && reads==2);
 avail=true;
 assert(a.ReadAfterFence(0,VK_SUCCESS,out) && reads==3);
 assert(out.count==1 && out.intervals_ns[0]==12.5);
 assert(a.BeginSlot(1,fake_cmd(),VK_SUCCESS));
 for(int i=0;i<4;i++){assert(a.BeginPair(1,fake_cmd()));assert(a.EndPair(1,fake_cmd()));}
 assert(!a.BeginPair(1,fake_cmd()));
 assert(writes==10);
 assert(write_indices[2]==8 && write_indices[9]==15);
 assert(a.Submitted(1,VK_SUCCESS));
 assert(a.ReadAfterFence(1,VK_SUCCESS,out));
 assert(out.count==4);
 assert(!a.DestroyAfterDeviceIdle(false)&&destroys==0);
 idle_result=VK_ERROR_DEVICE_LOST;
 assert(!a.DestroyAfterDeviceIdle(true)&&destroys==0);
 idle_result=VK_SUCCESS;
 assert(a.DestroyAfterDeviceIdle(true));
 assert(destroys==1 && !a.Enabled());
 // submit errors disable diagnostic, requiring later device idle for cleanup
 assert(a.Create(fake_device(),f,true,2,32,2.5f));
 assert(a.BeginSlot(0,fake_cmd(),VK_SUCCESS));
 assert(!a.Submitted(0,VK_ERROR_DEVICE_LOST));
 assert(!a.Enabled() && a.DestroyAfterDeviceIdle(true));
 assert(destroys==2);
 // query read failures disable: do not pretend timestamps are valid
 assert(a.Create(fake_device(),f,true,2,32,2.5f));
 assert(a.BeginSlot(0,fake_cmd(),VK_SUCCESS));
 assert(a.BeginPair(0,fake_cmd()) && a.EndPair(0,fake_cmd()));
 assert(a.Submitted(0,VK_SUCCESS));
 read_result=VK_ERROR_DEVICE_LOST;
 assert(!a.ReadAfterFence(0,VK_SUCCESS,out));
 assert(!a.Enabled());
 assert(a.DestroyAfterDeviceIdle(true));assert(destroys==3);
 std::cout<<"PRE671H_NATIVE_VULKAN_PFN_HOST_MOCK_TEST=PASS\n"
          <<"PRE671H_REAL_VK_OBJECT_CREATED=false\n"
          <<"PRE671H_UNCHECKED_FENCE_READ_REJECTED=true\n"
          <<"PRE671H_PFN_ABI_TYPED=PASS\n"
          <<"PRE671H_READ_AVAILABILITY_GUARD=PASS\n"
          <<"PRE671H_MOCK_QUERY_OFFSETS=PASS\n"
          <<"PRE671H_DRIVER_GPU_TESTED=false\n"
          <<"PRE671H_MULTIVIEW_UNTESTED=true\n"
          <<"PRE671H_PER_TILE_MODE_UNTESTED=true\n"
          <<"PRE671H_APK_BUILT=false\n"
          <<"PRE671H_FPS_GAIN_PROVEN=false\n";
}
